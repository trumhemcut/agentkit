import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder
from api.models import RunAgentInput, CanvasMessageRequest, ArtifactUpdate
from graphs.chat_graph import create_chat_graph
from graphs.canvas_graph import create_canvas_graph
from llm.ollama_client import ollama_client
from agents.agent_registry import agent_registry
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


@router.get("/models")
async def list_models():
    """List available Ollama models"""
    try:
        models_data = await ollama_client.list_available_models()
        return models_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.post("/chat")
async def chat_endpoint(input_data: RunAgentInput, request: Request):
    """AG-UI compliant chat endpoint with SSE streaming using chat_graph"""
    # Validate agent exists and is available BEFORE starting streaming
    if not agent_registry.is_available(input_data.agent):
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{input_data.agent}' not available"
        )
    
    accept_header = request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)
    
    async def event_generator():
        # Send RUN_STARTED event using official AG-UI event class
        yield encoder.encode(
            RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
        )
        
        try:
            # Select appropriate agent/graph based on agent parameter
            if input_data.agent == "chat":
                # Use chat graph with event callback pattern
                graph = create_chat_graph(model=input_data.model)
                state = {
                    "messages": [msg.model_dump() for msg in input_data.messages],
                    "thread_id": input_data.thread_id,
                    "run_id": input_data.run_id
                }
                
                # Create event queue for streaming
                import asyncio
                event_queue = asyncio.Queue()
                
                async def event_callback(event):
                    """Callback to receive events from agent"""
                    await event_queue.put(event)
                
                # Run graph with event callback in background
                async def run_graph():
                    config = {
                        "configurable": {
                            "event_callback": event_callback
                        }
                    }
                    await graph.ainvoke(state, config=config)
                    await event_queue.put(None)  # Signal completion
                
                graph_task = asyncio.create_task(run_graph())
                
                # Stream events as they arrive
                while True:
                    event = await event_queue.get()
                    if event is None:  # Completion signal
                        break
                    yield encoder.encode(event)
                
                # Wait for graph to complete
                await graph_task
                
            elif input_data.agent == "canvas":
                # Use canvas agent directly for streaming (similar to /canvas/stream endpoint)
                from agents.canvas_agent import CanvasAgent
                from agents.chat_agent import ChatAgent
                from graphs.canvas_graph import detect_intent_node, route_to_handler
                
                # Prepare state with canvas-specific fields
                state = {
                    "messages": [msg.model_dump() for msg in input_data.messages],
                    "thread_id": input_data.thread_id,
                    "run_id": input_data.run_id,
                    "artifact": None,
                    "selectedText": None,
                    "artifactAction": None
                }
                
                # Detect intent to determine routing
                try:
                    state = detect_intent_node(state)
                    route = route_to_handler(state)
                except Exception as e:
                    logger.warning(f"Error in intent detection, defaulting to chat: {e}")
                    route = "chat_only"
                
                # Route to appropriate agent
                if route == "artifact_action":
                    canvas_agent = CanvasAgent(model=input_data.model)
                    async for event in canvas_agent.run(state):
                        yield encoder.encode(event)
                else:
                    chat_agent = ChatAgent(model=input_data.model)
                    async for event in chat_agent.run(state):
                        yield encoder.encode(event)
            else:
                raise ValueError(f"Unknown agent: {input_data.agent}")
            
            # Send RUN_FINISHED event using official AG-UI event class
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
            
            # Send RUN_ERROR event using official AG-UI event class
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


# Canvas routes
@router.post("/canvas/stream")
async def canvas_stream_endpoint(input_data: CanvasMessageRequest, request: Request):
    """Canvas agent endpoint with artifact streaming"""
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
            # Prepare state
            state = {
                "messages": [msg.model_dump() for msg in input_data.messages],
                "thread_id": input_data.thread_id,
                "run_id": input_data.run_id,
                "artifact": input_data.artifact.model_dump() if input_data.artifact else None,
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
    """Manually update artifact content (for future implementation)"""
    # This endpoint would persist artifacts to a database
    # For now, return a placeholder response
    return {
        "success": True,
        "artifact_id": artifact_id,
        "message": "Artifact update endpoint (to be implemented with persistence)"
    }


@router.get("/canvas/artifacts/{artifact_id}/versions")
async def get_artifact_versions_endpoint(artifact_id: str):
    """Get version history for artifact (for future implementation)"""
    # This endpoint would retrieve artifact history from database
    # For now, return a placeholder response
    return {
        "artifact_id": artifact_id,
        "versions": [],
        "message": "Artifact version history (to be implemented with persistence)"
    }

