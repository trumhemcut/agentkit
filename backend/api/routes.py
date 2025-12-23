from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder
from api.models import RunAgentInput, CanvasMessageRequest, ArtifactUpdate
from graphs.chat_graph import create_chat_graph
from graphs.canvas_graph import create_canvas_graph
from llm.ollama_client import ollama_client

router = APIRouter()


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
    """AG-UI compliant chat endpoint with SSE streaming"""
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
            # Create chat agent directly for streaming with optional model
            from agents.chat_agent import ChatAgent
            chat_agent = ChatAgent(model=input_data.model)
            
            state = {
                "messages": [msg.model_dump() for msg in input_data.messages],
                "thread_id": input_data.thread_id,
                "run_id": input_data.run_id
            }
            
            # Stream agent events directly
            async for event in chat_agent.run(state):
                yield encoder.encode(event)
            
            # Send RUN_FINISHED event using official AG-UI event class
            yield encoder.encode(
                RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id
                )
            )
        
        except Exception as e:
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
            
            # Check if this should route to canvas agent or chat
            try:
                from graphs.canvas_graph import detect_intent_node, route_to_handler
                state = detect_intent_node(state)
                route = route_to_handler(state)
            except Exception as e:
                print(f"[Canvas] Error in intent detection, defaulting to chat: {e}")
                route = "chat_only"
            
            if route == "artifact_action":
                # Use canvas agent for streaming
                try:
                    from agents.canvas_agent import CanvasAgent
                    canvas_agent = CanvasAgent(model=input_data.model)
                    
                    async for event in canvas_agent.run(state):
                        yield encoder.encode(event)
                except Exception as e:
                    print(f"[Canvas] Error in canvas agent, falling back to chat: {e}")
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

