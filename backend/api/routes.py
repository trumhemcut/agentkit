from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder
from api.models import RunAgentInput
from graphs.chat_graph import create_chat_graph

router = APIRouter()


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
            # Create chat agent directly for streaming
            from agents.chat_agent import ChatAgent
            chat_agent = ChatAgent()
            
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
