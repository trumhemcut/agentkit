"""
Agent Router

Handles agent-related endpoints:
- List available agents
- Handle user actions from A2UI components
- Retry message generation
"""
import logging
import asyncio
import uuid
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder
from api.models import UserActionRequest, RunAgentInput, Message as APIMessage
from api.utils.state_preparation import prepare_state_for_agent
from agents.agent_registry import agent_registry
from graphs.graph_factory import graph_factory
from database.config import get_db
from database.models import Message as DBMessage
from services.message_service import MessageService
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/agents")
async def list_agents():
    """List available agents with metadata"""
    try:
        agents = agent_registry.list_agents(available_only=True)
        
        return {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "icon": agent.icon,
                    "sub_agents": agent.sub_agents,
                    "features": agent.features
                }
                for agent in agents
            ],
            "default": settings.DEFAULT_AGENT  # Use config default
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching agents: {str(e)}"
        )


@router.post("/agents/{agent_id}/action")
async def handle_user_action(
    agent_id: str,
    request_data: UserActionRequest,
    http_request: Request
):
    """
    Handle user actions from A2UI components.
    
    This endpoint receives userAction messages when users interact with 
    actionable components (buttons, form submissions, etc.) in the A2UI interface.
    
    Args:
        agent_id: Agent identifier ("a2ui_agent", "a2ui-loop", etc.)
        request_data: UserActionRequest containing userAction payload
        http_request: FastAPI request object
        
    Returns:
        StreamingResponse with AG-UI events and A2UI updates
        
    Example:
        POST /agents/a2ui-loop/action
        {
            "userAction": {
                "name": "submit_form",
                "surfaceId": "contact_form",
                "sourceComponentId": "submit_button",
                "timestamp": "2025-12-30T10:30:00Z",
                "context": {
                    "email": "user@example.com",
                    "name": "John Doe"
                }
            },
            "threadId": "thread-123",
            "runId": "run-456"
        }
    """
    logger.info(f"Received userAction for agent={agent_id}: {request_data.user_action.name}")
    
    # Validate agent exists and is available
    agent_info = agent_registry.get_agent(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Check if agent supports A2UI (either "a2ui" or "a2ui-protocol" feature)
    if "a2ui" not in agent_info.features and "a2ui-protocol" not in agent_info.features:
        raise HTTPException(
            status_code=400, 
            detail=f"Agent {agent_id} does not support A2UI actions"
        )
    
    accept_header = http_request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)
    
    async def event_generator():
        try:
            # Send RUN_STARTED event
            yield encoder.encode(
                RunStartedEvent(
                    type=EventType.RUN_STARTED,
                    thread_id=request_data.thread_id,
                    run_id=request_data.run_id
                )
            )
            
            # Get or create graph
            graph = graph_factory.create_graph(
                agent_id=agent_id,
                model=request_data.model,
                provider=request_data.provider
            )
            
            # Prepare state with user action
            state = {
                "messages": [],  # No user text message
                "thread_id": request_data.thread_id,
                "run_id": request_data.run_id,
                "user_action": request_data.user_action.model_dump(by_alias=True)  # Add user action to state
            }
            
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
                if await http_request.is_disconnected():
                    logger.info(f"Client disconnected for action={request_data.user_action.name}, run_id={request_data.run_id}, cancelling graph")
                    graph_task.cancel()
                    break
                
                try:
                    # Wait for event with shorter timeout for faster disconnect detection
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.05)
                    
                    # Check disconnect again BEFORE yielding
                    if await http_request.is_disconnected():
                        logger.info(f"Client disconnected before yielding event, cancelling graph")
                        graph_task.cancel()
                        break
                    
                    # Check if event is already encoded (string) or needs encoding
                    if isinstance(event, str):
                        # Already encoded (e.g., from A2UI agent)
                        yield event
                    else:
                        # Needs encoding (AG-UI BaseEvent or dict)
                        if isinstance(event, dict):
                            # A2UI message or custom event dict
                            # For A2UI messages, we need to wrap them in AG-UI DATA event
                            from ag_ui.core import DataEvent
                            data_event = DataEvent(
                                type=EventType.DATA,
                                thread_id=request_data.thread_id,
                                run_id=request_data.run_id,
                                data=event
                            )
                            yield encoder.encode(data_event)
                        else:
                            yield encoder.encode(event)
                except asyncio.TimeoutError:
                    # No event yet, continue to check disconnect in next iteration
                    continue
            
            # Wait for graph to complete
            await graph_task
            
            # Check if there was an error during graph execution
            if graph_error:
                raise graph_error
            
            # Send RUN_FINISHED event
            yield encoder.encode(
                RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=request_data.thread_id,
                    run_id=request_data.run_id
                )
            )
        
        except GeneratorExit:
            # Client disconnected (e.g., user clicked Stop button)
            logger.info(f"[AGENTS_ROUTER] Client disconnected for agent={agent_id}, action={request_data.user_action.name}, run_id={request_data.run_id}")
            # FastAPI will handle cleanup automatically
        
        except Exception as e:
            # Log error for debugging
            import traceback
            logger.error(f"[AGENTS_ROUTER] Error processing user action for agent={agent_id}: {e}")
            logger.error(f"[AGENTS_ROUTER] Traceback: {traceback.format_exc()}")
            
            # Send RUN_ERROR event
            yield encoder.encode(
                RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    thread_id=request_data.thread_id,
                    run_id=request_data.run_id,
                    message=str(e)
                )
            )
    
    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type()
    )


@router.post("/agents/{agent_id}/retry/{thread_id}/{message_id}")
async def retry_message(
    agent_id: str,
    thread_id: str,
    message_id: str,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Retry generating a response for a specific assistant message.
    
    This will:
    1. Find the user message that preceded the given assistant message
    2. Delete the assistant message (and its feedback if any)
    3. Re-run the agent with the same user message
    
    Args:
        agent_id: Agent identifier (e.g., "chat", "canvas")
        thread_id: Thread identifier
        message_id: ID of the assistant message to retry
        http_request: FastAPI request object
        db: Database session
        
    Returns:
        StreamingResponse with new response via SSE
    """
    logger.info(f"Retry message request: agent={agent_id}, thread={thread_id}, message={message_id}")
    
    # Validate agent exists and is available
    if not agent_registry.is_available(agent_id):
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{agent_id}' not available"
        )
    
    # Get the message to retry
    message = await MessageService.get_message(db, message_id)
    if not message or message.role != "assistant":
        raise HTTPException(status_code=404, detail="Assistant message not found")
    
    if message.thread_id != thread_id:
        raise HTTPException(status_code=400, detail="Message does not belong to this thread")
    
    # Find all messages before this one, ordered by created_at
    from sqlalchemy import select
    result = await db.execute(
        select(DBMessage)
        .filter(
            DBMessage.thread_id == thread_id,
            DBMessage.created_at < message.created_at
        )
        .order_by(DBMessage.created_at.asc())
    )
    previous_messages = result.scalars().all()
    
    if not previous_messages:
        raise HTTPException(status_code=400, detail="No previous messages found to retry from")
    
    # Delete the assistant message (CASCADE will delete feedback)
    await MessageService.delete_message(db, message_id)
    
    # Reconstruct conversation history for the agent
    messages_for_agent = []
    for msg in previous_messages:
        messages_for_agent.append(APIMessage(
            role=msg.role,
            content=msg.content or "",
            message_type=msg.message_type
        ))
    
    # Create input for re-running the agent
    run_id = str(uuid.uuid4())
    input_data = RunAgentInput(
        thread_id=thread_id,
        run_id=run_id,
        messages=messages_for_agent,
        agent=agent_id
    )
    
    # Prepare SSE streaming
    accept_header = http_request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)
    
    async def event_generator():
        try:
            # Send RUN_STARTED event
            yield encoder.encode(
                RunStartedEvent(
                    type=EventType.RUN_STARTED,
                    thread_id=thread_id,
                    run_id=run_id
                )
            )
            
            # Create graph dynamically based on agent_id
            graph = graph_factory.create_graph(agent_id=agent_id)
            
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
                # Check disconnect
                if await http_request.is_disconnected():
                    logger.info(f"Client disconnected for retry, thread={thread_id}, cancelling graph")
                    graph_task.cancel()
                    break
                
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.05)
                    
                    # Check disconnect again before yielding
                    if await http_request.is_disconnected():
                        logger.info(f"Client disconnected before yielding event, cancelling graph")
                        graph_task.cancel()
                        break
                    
                    # Encode and yield event
                    if isinstance(event, str):
                        yield event
                    else:
                        if isinstance(event, dict):
                            from ag_ui.core import DataEvent
                            data_event = DataEvent(
                                type=EventType.DATA,
                                thread_id=thread_id,
                                run_id=run_id,
                                data=event
                            )
                            yield encoder.encode(data_event)
                        else:
                            yield encoder.encode(event)
                except asyncio.TimeoutError:
                    continue
            
            # Wait for graph to complete
            await graph_task
            
            # Check if there was an error
            if graph_error:
                raise graph_error
            
            # Send RUN_FINISHED event
            yield encoder.encode(
                RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=thread_id,
                    run_id=run_id
                )
            )
        
        except GeneratorExit:
            logger.info(f"Client disconnected for retry, thread={thread_id}")
        
        except Exception as e:
            import traceback
            logger.error(f"Error during message retry: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Send RUN_ERROR event
            yield encoder.encode(
                RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    thread_id=thread_id,
                    run_id=run_id,
                    message=str(e)
                )
            )
    
    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type()
    )

