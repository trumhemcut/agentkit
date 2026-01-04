import logging
import json
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder
from api.models import (
    RunAgentInput, CanvasMessageRequest, ArtifactUpdate, UserActionRequest,
    ThreadCreate, ThreadUpdate, ThreadResponse, ThreadListResponse,
    MessageCreate, MessageResponse, MessageListResponse, DeleteResponse
)
from graphs.graph_factory import graph_factory
from llm.provider_client import provider_client
from agents.agent_registry import agent_registry
from config import settings
from cache.artifact_cache import artifact_cache
from database.config import get_db
from services.thread_service import ThreadService
from services.message_service import MessageService

logger = logging.getLogger(__name__)
router = APIRouter()


def prepare_state_for_agent(agent_id: str, input_data: RunAgentInput) -> dict:
    """
    Prepare initial state dictionary for graph execution
    
    Args:
        agent_id: Agent identifier ("chat", "canvas", etc.)
        input_data: Request data with messages, thread_id, run_id
        
    Returns:
        State dict matching the agent's StateGraph schema
    """
    # Base state for all agents
    state = {
        "messages": [
            {"role": msg.role, "content": msg.content} 
            for msg in input_data.messages
        ],
        "thread_id": input_data.thread_id,
        "run_id": input_data.run_id
    }
    
    # Agent-specific state extensions
    if agent_id == "canvas":
        # Canvas agent needs additional artifact state
        selected_text_data = input_data.selectedText.model_dump() if input_data.selectedText else None
        
        # Diagnostic logging for selection tracking
        if selected_text_data:
            logger.info(f"[ROUTES] Received selectedText in request: start={selected_text_data.get('start')}, end={selected_text_data.get('end')}")
            logger.info(f"[ROUTES] Selected text preview: '{selected_text_data.get('text', '')[:100]}...'")
        else:
            logger.debug(f"[ROUTES] No selectedText in request")
        
        state.update({
            "artifact": input_data.artifact.model_dump() if input_data.artifact else None,
            "selectedText": selected_text_data,
            "artifact_id": input_data.artifact_id,
            "artifactAction": input_data.action  # Will be detected by canvas graph if None
        })
        
        logger.debug(f"[ROUTES] Canvas state prepared with artifact_id={input_data.artifact_id}, action={input_data.action}")
    
    return state


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


@router.get("/models")
async def list_models():
    """List available models from all providers"""
    try:
        models_data = await provider_client.list_all_models()
        return models_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.get("/models/{provider}")
async def list_provider_models(provider: str):
    """List models from a specific provider"""
    try:
        models = await provider_client.get_models_by_provider(provider)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


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
        import asyncio
        
        try:
            # Send RUN_STARTED event
            yield encoder.encode(
                RunStartedEvent(
                    type=EventType.RUN_STARTED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id
                )
            )
            
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
                try:
                    # Wait for event with timeout to check if graph is done
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    
                    # Check if event is already encoded (string) or needs encoding
                    if isinstance(event, str):
                        # Already encoded (e.g., from A2UI agent)
                        yield event
                    else:
                        # Needs encoding (AG-UI BaseEvent)
                        yield encoder.encode(event)
                except asyncio.TimeoutError:
                    # No event yet, check if graph is done
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
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id
                )
            )
        
        except GeneratorExit:
            # Client disconnected (e.g., user clicked Stop button)
            logger.info(f"[ROUTES] Client disconnected for agent={agent_id}, run_id={input_data.run_id}, thread_id={input_data.thread_id}")
            # FastAPI will handle cleanup automatically
            # Graph execution will be cancelled when generator is closed
        
        except Exception as e:
            # Log error for debugging
            import traceback
            logger.error(f"[ROUTES] Error occurred in agent={agent_id}, run_id={input_data.run_id}: {e}")
            logger.error(f"[ROUTES] Traceback: {traceback.format_exc()}")
            
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
        import asyncio
        
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
                try:
                    # Wait for event with timeout to check if graph is done
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    
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
                    # No event yet, check if graph is done
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
            logger.info(f"[ROUTES] Client disconnected for agent={agent_id}, action={request_data.user_action.name}, run_id={request_data.run_id}")
            # FastAPI will handle cleanup automatically
        
        except Exception as e:
            # Log error for debugging
            import traceback
            logger.error(f"[ROUTES] Error processing user action for agent={agent_id}: {e}")
            logger.error(f"[ROUTES] Traceback: {traceback.format_exc()}")
            
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


# Canvas routes (DEPRECATED - Use /chat/canvas-agent instead)
@router.post("/canvas/stream")
async def canvas_stream_endpoint(input_data: CanvasMessageRequest, request: Request):
    """
    DEPRECATED: Canvas agent endpoint with artifact streaming.
    
    Use /chat/canvas-agent endpoint instead. This endpoint is maintained for backward compatibility
    but will be removed in a future version.
    
    The new /chat/canvas-agent endpoint uses unified TEXT_MESSAGE protocol with artifact metadata,
    providing better integration with the main chat interface.
    """
    logger.warning("DEPRECATED: /canvas/stream endpoint called. Please migrate to /chat/canvas-agent")
    
    # Validate agent exists and is available BEFORE starting streaming
    if not agent_registry.is_available(input_data.agent):
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{input_data.agent}' not available"
        )
    
    accept_header = request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)
    
    async def event_generator():
        try:
            # Send RUN_STARTED event
            yield encoder.encode(
                RunStartedEvent(
                    type=EventType.RUN_STARTED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id
                )
            )
            
            # Handle artifact retrieval: prioritize artifact_id over artifact
            artifact = None
            if input_data.artifact_id:
                # Retrieve from cache using artifact_id
                artifact = artifact_cache.get(input_data.artifact_id)
                if not artifact:
                    logger.warning(f"Artifact ID provided but not found in cache: {input_data.artifact_id}")
            elif input_data.artifact:
                # Legacy: client sent full artifact (will be deprecated)
                logger.warning("Client sent full artifact instead of artifact_id. Consider updating frontend.")
                artifact = input_data.artifact.model_dump()
            
            # Prepare state
            state = {
                "messages": [msg.model_dump() for msg in input_data.messages],
                "thread_id": input_data.thread_id,
                "run_id": input_data.run_id,
                "artifact": artifact,
                "artifact_id": input_data.artifact_id,  # Pass artifact_id to agent
                "selectedText": input_data.selectedText.model_dump() if input_data.selectedText else None,
                "artifactAction": input_data.action
            }
            
            # Determine which agent to use based on request parameter or intent detection
            use_canvas = False
            
            if input_data.agent == "canvas":
                # User explicitly selected canvas agent
                use_canvas = True
                logger.info(f"Using canvas agent (explicitly selected)")
                
                # If action is not provided, run intent detection to determine it
                if input_data.action is None:
                    logger.info(f"No action provided, running intent detection")
                    try:
                        from graphs.canvas_graph import detect_intent_node
                        state = detect_intent_node(state)
                        logger.info(f"Intent detection set action to: {state.get('artifactAction')}")
                    except Exception as e:
                        logger.warning(f"Error in intent detection: {e}")
                        # Default to create if no artifact, update if artifact exists
                        if state.get("artifact"):
                            state["artifactAction"] = "update"
                        else:
                            state["artifactAction"] = "create"
                        logger.info(f"Defaulted to action: {state['artifactAction']}")
            else:
                # Fall back to intent detection
                try:
                    from graphs.canvas_graph import detect_intent_node, route_to_handler
                    state = detect_intent_node(state)
                    route = route_to_handler(state)
                    use_canvas = (route == "artifact_action")
                    logger.info(f"Intent detection route: {route}")
                except Exception as e:
                    logger.warning(f"Error in intent detection, defaulting to chat: {e}")
                    use_canvas = False
            
            if use_canvas:
                # Use canvas agent for streaming
                try:
                    from agents.canvas_agent import CanvasAgent
                    canvas_agent = CanvasAgent(model=input_data.model)
                    
                    async for event in canvas_agent.run(state):
                        yield encoder.encode(event)
                except Exception as e:
                    logger.error(f"Error in canvas agent, falling back to chat: {e}")
                    # Fall back to chat agent
                    from agents.chat_agent import ChatAgent
                    chat_agent = ChatAgent(model=input_data.model)
                    
                    async for event in chat_agent.run(state):
                        yield encoder.encode(event)
            else:
                # Use regular chat agent
                from agents.chat_agent import ChatAgent
                chat_agent = ChatAgent(model=input_data.model)
                
                async for event in chat_agent.run(state):
                    yield encoder.encode(event)
            
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
            logger.info(f"[ROUTES] Client disconnected for canvas endpoint, run_id={input_data.run_id}")
            # FastAPI will handle cleanup automatically
        
        except Exception as e:
            # Log error for debugging
            import traceback
            logger.error(f"[ROUTES] Error occurred in canvas endpoint: {e}")
            logger.error(f"[ROUTES] Traceback: {traceback.format_exc()}")
            
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


@router.post("/canvas/artifacts/{artifact_id}")
async def update_artifact_endpoint(artifact_id: str, updates: ArtifactUpdate):
    """Manually update artifact content"""
    try:
        # Get existing artifact from cache
        artifact = artifact_cache.get(artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")
        
        # Update artifact content
        updated_artifact = {
            "artifact_id": artifact_id,
            "title": artifact.get("title", "Untitled"),
            "content": updates.content,
            "language": artifact.get("language")
        }
        
        # Update in cache
        success = artifact_cache.update(artifact_id, updated_artifact)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update artifact")
        
        return {
            "success": True,
            "artifact_id": artifact_id,
            "message": "Artifact updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/canvas/artifacts/{artifact_id}")
async def get_artifact_endpoint(artifact_id: str):
    """Get artifact by ID from cache"""
    try:
        artifact = artifact_cache.get(artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")
        
        return artifact
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/a2ui/stream")
async def a2ui_stream_endpoint(
    message: str = "Show me a checkbox",
    thread_id: str = None,
    request: Request = None
):
    """
    A2UI Agent endpoint for streaming interactive UI components.
    
    This endpoint demonstrates the A2UI (Agent-to-UI) protocol by generating
    interactive UI components (checkboxes, buttons, forms, etc.) that render
    natively in the frontend.
    
    The A2UI protocol complements AG-UI:
    - AG-UI: Real-time event streaming (text messages, status updates)
    - A2UI: Declarative UI component generation (checkboxes, forms, cards)
    
    Args:
        message: User message/query (default: "Show me a checkbox")
        thread_id: Optional thread ID for conversation context
        request: FastAPI request object
    
    Returns:
        StreamingResponse with mixed A2UI and AG-UI events
        
    Example:
        GET /a2ui/stream?message=Create a terms agreement checkbox
        
        Response (SSE format):
        data: {"type":"surfaceUpdate","surfaceId":"surface-abc",...}
        data: {"type":"dataModelUpdate","surfaceId":"surface-abc",...}
        data: {"type":"beginRendering","surfaceId":"surface-abc",...}
        data: {"type":"TEXT_MESSAGE_CONTENT","delta":"Check the box above"}
    """
    import uuid
    from agents.a2ui_agent import A2UIAgent
    
    # Generate IDs if not provided
    thread_id = thread_id or str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    
    logger.info(f"A2UI stream request - thread: {thread_id}, message: {message}")
    
    # Create A2UI agent
    agent = A2UIAgent()
    
    # Prepare state
    state = {
        "messages": [{"role": "user", "content": message}],
        "thread_id": thread_id,
        "run_id": run_id
    }
    
    async def event_generator():
        """Stream A2UI and AG-UI events"""
        try:
            # Stream events from agent
            async for event in agent.run(state):
                yield event
                
        except Exception as e:
            import traceback
            logger.error(f"Error in A2UI stream: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Send error event
            encoder = EventEncoder(accept="text/event-stream")
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
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============================================================================
# Database Persistence Endpoints
# ============================================================================

# Thread Endpoints
@router.post("/threads", response_model=ThreadResponse)
async def create_thread(
    data: ThreadCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new conversation thread.
    
    Request body:
        agent_type: str - Type of agent ("chat", "canvas", "salary_viewer")
        model: str - LLM model name
        provider: str - LLM provider name
        title: str (optional) - Thread title
    
    Returns:
        Thread object with id, title, agent_type, model, provider, timestamps
    """
    try:
        thread = await ThreadService.create_thread(
            db, data.agent_type, data.model, data.provider, data.title
        )
        return ThreadResponse.model_validate(thread)
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all conversation threads.
    
    Query params:
        limit: int - Maximum number of threads to return (default: 50)
        offset: int - Number of threads to skip (default: 0)
    
    Returns:
        List of thread objects ordered by updated_at DESC
    """
    try:
        threads = await ThreadService.list_threads(db, limit, offset)
        return ThreadListResponse(
            threads=[ThreadResponse.model_validate(t) for t in threads]
        )
    except Exception as e:
        logger.error(f"Error listing threads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific thread by ID.
    
    Path params:
        thread_id: str - Thread identifier
    
    Returns:
        Thread object with full details
    """
    try:
        thread = await ThreadService.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return ThreadResponse.model_validate(thread)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    data: ThreadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update thread metadata.
    
    Path params:
        thread_id: str - Thread identifier
    
    Request body:
        title: str (optional) - New thread title
    
    Returns:
        Updated thread details
    """
    try:
        thread = await ThreadService.update_thread(db, thread_id, data.title)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return ThreadResponse.model_validate(thread)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/threads/{thread_id}", response_model=DeleteResponse)
async def delete_thread(
    thread_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a thread and all associated messages.
    
    Path params:
        thread_id: str - Thread identifier
    
    Returns:
        Success message
    """
    try:
        success = await ThreadService.delete_thread(db, thread_id)
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return DeleteResponse(message="Thread deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Message Endpoints
@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def create_message(
    thread_id: str,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new message in a thread.
    
    Path params:
        thread_id: str - Thread identifier
    
    Request body:
        role: str - Message role ("user" or "assistant")
        content: str (optional) - Text content
        artifact_data: dict (optional) - A2UI artifact data
        metadata: dict (optional) - Additional metadata
    
    Returns:
        Created message object
    """
    try:
        # Verify thread exists
        thread = await ThreadService.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        message = await MessageService.create_message(
            db, thread_id, data.role, data.content, data.artifact_data, data.metadata
        )
        
        # Convert to response model
        return MessageResponse(
            id=message.id,
            thread_id=message.thread_id,
            role=message.role,
            content=message.content,
            artifact_data=json.loads(message.artifact_data) if message.artifact_data else None,
            metadata=json.loads(message.message_metadata) if message.message_metadata else None,
            created_at=message.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message in thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/{thread_id}/messages", response_model=MessageListResponse)
async def list_messages(
    thread_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    List all messages in a thread.
    
    Path params:
        thread_id: str - Thread identifier
    
    Returns:
        List of message objects ordered by created_at ASC
    """
    try:
        messages = await MessageService.list_messages(db, thread_id)
        return MessageListResponse(
            messages=[
                MessageResponse(
                    id=m.id,
                    thread_id=m.thread_id,
                    role=m.role,
                    content=m.content,
                    artifact_data=json.loads(m.artifact_data) if m.artifact_data else None,
                    metadata=json.loads(m.message_metadata) if m.message_metadata else None,
                    created_at=m.created_at
                )
                for m in messages
            ]
        )
    except Exception as e:
        logger.error(f"Error listing messages for thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{message_id}", response_model=DeleteResponse)
async def delete_message(
    message_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a message.
    
    Path params:
        message_id: str - Message identifier
    
    Returns:
        Success message
    """
    try:
        success = await MessageService.delete_message(db, message_id)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return DeleteResponse(message="Message deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
