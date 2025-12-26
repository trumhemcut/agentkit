import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder
from api.models import RunAgentInput, CanvasMessageRequest, ArtifactUpdate
from graphs.graph_factory import graph_factory
from llm.provider_client import provider_client
from agents.agent_registry import agent_registry
from config import settings
from cache.artifact_cache import artifact_cache

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
        state.update({
            "artifact": input_data.artifact.model_dump() if input_data.artifact else None,
            "selectedText": input_data.selectedText.model_dump() if input_data.selectedText else None,
            "artifact_id": input_data.artifact_id,
            "artifactAction": input_data.action  # Will be detected by canvas graph if None
        })
    
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
        
        # Send RUN_STARTED event
        yield encoder.encode(
            RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
        )
        
        try:
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
        
        except Exception as e:
            # Log error for debugging
            import traceback
            logger.error(f"Error occurred: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
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
        # Send RUN_STARTED event
        yield encoder.encode(
            RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
        )
        
        try:
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
        
        except Exception as e:
            # Log error for debugging
            import traceback
            logger.error(f"Error occurred: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
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

