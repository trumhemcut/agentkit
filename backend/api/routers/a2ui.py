"""
A2UI Router

Handles A2UI (Agent-to-UI) protocol endpoints for interactive UI components.
"""
import logging
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import EventType, RunErrorEvent
from ag_ui.encoder import EventEncoder
from agents.a2ui_agent import A2UIAgent

logger = logging.getLogger(__name__)
router = APIRouter()


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
