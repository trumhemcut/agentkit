"""
Test canvas agent streaming to verify events are emitted
"""
import asyncio
import logging
from agents.canvas_agent import CanvasAgent
from graphs.canvas_graph import CanvasGraphState

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_canvas_agent_streaming():
    """Test that canvas agent emits events properly"""
    agent = CanvasAgent(model="qwen:7b")
    
    state: CanvasGraphState = {
        "messages": [
            {"role": "user", "content": "Create a Python function to calculate fibonacci"}
        ],
        "thread_id": "test-thread",
        "run_id": "test-run",
        "artifact": None,
        "selectedText": None,
        "artifactAction": "create"
    }
    
    print("\n=== Testing Canvas Agent Streaming ===\n")
    
    event_count = 0
    async for event in agent.run(state):
        event_count += 1
        print(f"Event {event_count}: {event.type} - {getattr(event, 'name', 'N/A')}")
        if hasattr(event, 'value'):
            print(f"  Value keys: {list(event.value.keys()) if isinstance(event.value, dict) else 'N/A'}")
    
    print(f"\n=== Total events received: {event_count} ===")
    
    if event_count == 0:
        print("ERROR: No events were emitted!")
    else:
        print("SUCCESS: Events were emitted")


if __name__ == "__main__":
    asyncio.run(test_canvas_agent_streaming())
