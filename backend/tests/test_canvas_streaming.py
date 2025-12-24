"""
Test canvas agent streaming to verify TEXT_MESSAGE events are emitted with artifact metadata
"""
import asyncio
import logging
from agents.canvas_agent import CanvasAgent
from graphs.canvas_graph import CanvasGraphState
from ag_ui.core import EventType

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_canvas_agent_streaming():
    """Test that canvas agent emits TEXT_MESSAGE events with artifact metadata"""
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
    
    print("\n=== Testing Canvas Agent Streaming (New Protocol) ===\n")
    
    event_count = 0
    text_message_start_found = False
    artifact_metadata_found = False
    text_message_content_count = 0
    text_message_end_found = False
    
    async for event in agent.run(state):
        event_count += 1
        print(f"Event {event_count}: {event.type}")
        
        # Check for TEXT_MESSAGE_START with artifact metadata
        if event.type == EventType.TEXT_MESSAGE_START:
            text_message_start_found = True
            if hasattr(event, 'metadata') and event.metadata:
                print(f"  Metadata: {event.metadata}")
                if event.metadata.get('message_type') == 'artifact':
                    artifact_metadata_found = True
                    print(f"  ✓ Artifact metadata found!")
                    print(f"    - artifact_type: {event.metadata.get('artifact_type')}")
                    print(f"    - language: {event.metadata.get('language')}")
                    print(f"    - title: {event.metadata.get('title')}")
        
        # Check for TEXT_MESSAGE_CONTENT
        elif event.type == EventType.TEXT_MESSAGE_CONTENT:
            text_message_content_count += 1
            if hasattr(event, 'delta'):
                print(f"  Content delta: {event.delta[:50]}...")
        
        # Check for TEXT_MESSAGE_END
        elif event.type == EventType.TEXT_MESSAGE_END:
            text_message_end_found = True
            print(f"  ✓ Message stream completed")
    
    print(f"\n=== Test Results ===")
    print(f"Total events received: {event_count}")
    print(f"TEXT_MESSAGE_START found: {text_message_start_found}")
    print(f"Artifact metadata found: {artifact_metadata_found}")
    print(f"TEXT_MESSAGE_CONTENT chunks: {text_message_content_count}")
    print(f"TEXT_MESSAGE_END found: {text_message_end_found}")
    
    # Validate results
    success = all([
        event_count > 0,
        text_message_start_found,
        artifact_metadata_found,
        text_message_content_count > 0,
        text_message_end_found
    ])
    
    if success:
        print("\n✓ SUCCESS: Canvas agent emits TEXT_MESSAGE events with artifact metadata!")
    else:
        print("\n✗ FAILURE: Canvas agent did not emit expected events")
        if not text_message_start_found:
            print("  - Missing TEXT_MESSAGE_START event")
        if not artifact_metadata_found:
            print("  - Missing artifact metadata in TEXT_MESSAGE_START")
        if text_message_content_count == 0:
            print("  - No TEXT_MESSAGE_CONTENT chunks received")
        if not text_message_end_found:
            print("  - Missing TEXT_MESSAGE_END event")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(test_canvas_agent_streaming())
    exit(0 if success else 1)
