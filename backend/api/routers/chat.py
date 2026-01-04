"""
Chat Router

Handles chat endpoints for all agents with SSE streaming support.
Supports unified chat interface for text and artifact generation.
"""
import logging
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder
from api.models import RunAgentInput
from api.utils.state_preparation import prepare_state_for_agent
from agents.agent_registry import agent_registry
from graphs.graph_factory import graph_factory
from database.config import AsyncSessionLocal
from services.message_service import MessageService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat")
async def chat_endpoint_legacy(input_data: RunAgentInput, request: Request):
    """
    DEPRECATED: Legacy chat endpoint without agent_id in path.
    
    Use /chat/{agent_id} endpoint instead. This endpoint is maintained for backward compatibility
    but will be removed in a future version.
    
    Redirects to appropriate agent based on input_data.agent field.
    """
    logger.warning("DEPRECATED: /chat endpoint called. Please migrate to /chat/{agent_id}")
    
    # Map old agent names to registry agent_id format
    agent_mapping = {
        "chat": "chat",
        "canvas": "canvas",
        "chat-agent": "chat",
        "canvas-agent": "canvas"
    }
    
    agent_id = agent_mapping.get(input_data.agent or "chat", "chat")
    
    # Forward to the new unified endpoint
    return await chat_endpoint(agent_id, input_data, request)


@router.post("/chat/{agent_id}")
async def chat_endpoint(agent_id: str, input_data: RunAgentInput, request: Request):
    """AG-UI compliant unified chat endpoint with SSE streaming.
    
    Supports all agents through single endpoint:
    - /chat/chat: Text-only conversations (ChatAgent)
    - /chat/canvas: Text + artifact generation (CanvasAgent)
    
    All agents are executed through LangGraph workflows for consistent behavior.
    
    Args:
        agent_id: Agent identifier (e.g., 'chat', 'canvas')
        input_data: Chat request with messages, thread_id, run_id, optional model
        request: FastAPI request object
    
    Returns:
        StreamingResponse with AG-UI protocol events
    """
    # Validate agent exists and is available
    if not agent_registry.is_available(agent_id):
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{agent_id}' not available"
        )
    
    accept_header = request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)
    
    async def event_generator():
        # Variables to track messages for persistence
        assistant_response_content = []
        has_artifact = False  # Track if an artifact was created
        artifact_metadata = {}  # Store artifact metadata
        
        try:
            # Send RUN_STARTED event
            yield encoder.encode(
                RunStartedEvent(
                    type=EventType.RUN_STARTED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id
                )
            )
            
            # Note: User messages are saved by frontend via /threads/{thread_id}/messages endpoint
            # Backend only needs to save assistant responses
            
            # Create graph dynamically based on agent_id
            graph = graph_factory.create_graph(
                agent_id=agent_id,
                model=input_data.model,
                provider=input_data.provider
            )
            
            # Prepare state based on agent type
            state = prepare_state_for_agent(agent_id, input_data)
            
            # Use async queue for real-time streaming
            event_queue = asyncio.Queue()
            graph_done = asyncio.Event()
            graph_error = None
            
            async def event_callback(event):
                """Callback invoked by graph nodes for streaming events"""
                await event_queue.put(event)
            
            async def run_graph():
                """Execute graph in background"""
                nonlocal graph_error
                try:
                    config = {"configurable": {"event_callback": event_callback}}
                    await graph.ainvoke(state, config)
                except Exception as e:
                    graph_error = e
                finally:
                    graph_done.set()
            
            # Start graph execution in background
            graph_task = asyncio.create_task(run_graph())
            
            # Stream events as they arrive
            while not graph_done.is_set() or not event_queue.empty():
                # Check disconnect BEFORE waiting for event
                if await request.is_disconnected():
                    logger.info(f"Client disconnected for run_id={input_data.run_id}, cancelling graph")
                    graph_task.cancel()
                    break
                
                try:
                    # Wait for event with shorter timeout for faster disconnect detection
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.05)
                    
                    # Track assistant response content for persistence
                    if hasattr(event, 'type'):
                        if event.type == EventType.TEXT_MESSAGE_CONTENT:
                            if hasattr(event, 'delta'):
                                assistant_response_content.append(event.delta)
                        
                        # Detect artifact creation (TEXT_MESSAGE_START with artifact metadata)
                        elif event.type == EventType.TEXT_MESSAGE_START:
                            event_dict = event if isinstance(event, dict) else (event.model_dump() if hasattr(event, 'model_dump') else {})
                            metadata = event_dict.get('metadata', {})
                            if metadata.get('message_type') == 'artifact':
                                has_artifact = True
                                artifact_metadata = {
                                    'type': metadata.get('artifact_type'),
                                    'language': metadata.get('language'),
                                    'title': metadata.get('title'),
                                    'id': metadata.get('artifact_id')
                                }
                                logger.info(f"Detected artifact creation: {artifact_metadata.get('id')}")
                    
                    # Check disconnect again BEFORE yielding
                    if await request.is_disconnected():
                        logger.info(f"Client disconnected before yielding event, cancelling graph")
                        graph_task.cancel()
                        break
                    
                    # Check if event is already encoded (string) or needs encoding
                    if isinstance(event, str):
                        # Already encoded (e.g., from A2UI agent)
                        yield event
                    else:
                        # Needs encoding (AG-UI BaseEvent)
                        yield encoder.encode(event)
                except asyncio.TimeoutError:
                    # No event yet, continue to check disconnect in next iteration
                    continue
            
            # Wait for graph to complete
            await graph_task
            
            # Check if there was an error during graph execution
            if graph_error:
                raise graph_error
            
            # Persist assistant response to database
            try:
                async with AsyncSessionLocal() as db:
                    if assistant_response_content:
                        full_response = "".join(assistant_response_content)
                        
                        # Determine message type based on artifact detection
                        message_type = "artifact" if has_artifact else "text"
                        
                        # Prepare artifact_data if artifact was created
                        artifact_data = None
                        if has_artifact and artifact_metadata:
                            artifact_data = artifact_metadata
                        
                        await MessageService.create_message(
                            db,
                            input_data.thread_id,
                            agent_id,
                            "assistant",
                            full_response,
                            message_type,
                            artifact_data
                        )
                        logger.info(f"Saved assistant response to thread {input_data.thread_id} with type={message_type}")
            except Exception as e:
                logger.error(f"Failed to save assistant response: {e}")
                # Don't fail the request if save fails
            
            # Send RUN_FINISHED event
            yield encoder.encode(
                RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id
                )
            )
        
        except GeneratorExit:
            # Client disconnected (e.g., user clicked Stop button)
            logger.info(f"[CHAT_ROUTER] Client disconnected for agent={agent_id}, run_id={input_data.run_id}, thread_id={input_data.thread_id}")
            
            # Save interrupted message to database
            try:
                async with AsyncSessionLocal() as db:
                    if assistant_response_content:
                        full_response = "".join(assistant_response_content)
                        
                        # Determine message type
                        message_type = "artifact" if has_artifact else "text"
                        artifact_data = None
                        if has_artifact and artifact_metadata:
                            artifact_data = artifact_metadata
                        
                        await MessageService.create_message(
                            db,
                            input_data.thread_id,
                            agent_id,
                            "assistant",
                            full_response,
                            message_type,
                            artifact_data,
                            None,  # metadata
                            True   # is_interrupted
                        )
                        logger.info(f"Saved interrupted assistant response to thread {input_data.thread_id}")
            except Exception as e:
                logger.error(f"Failed to save interrupted message: {e}")
            
            # FastAPI will handle cleanup automatically
            # Graph execution will be cancelled when generator is closed
        
        except Exception as e:
            # Log error for debugging
            import traceback
            logger.error(f"[CHAT_ROUTER] Error occurred in agent={agent_id}, run_id={input_data.run_id}: {e}")
            logger.error(f"[CHAT_ROUTER] Traceback: {traceback.format_exc()}")
            
            # Send RUN_ERROR event
            yield encoder.encode(
                RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id,
                    message=str(e)
                )
            )
    
    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type()
    )
