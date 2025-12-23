"""
Test canvas agent two-step process: artifact streaming + chat summary
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.canvas_agent import CanvasAgent
from ag_ui.core import EventType


async def test_two_step_artifact_creation():
    """Test that canvas agent streams both artifact and summary"""
    print("Testing two-step artifact creation...")
    
    agent = CanvasAgent()
    
    state = {
        "messages": [{"role": "user", "content": "Write a Python hello function"}],
        "thread_id": "test",
        "run_id": "test",
        "artifact": None,
        "selectedText": None,
        "artifactAction": "create"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
        print(f"  Event: {event.type} - {getattr(event, 'name', '')} {getattr(event, 'message_id', '')}")
    
    # Check we got the expected events
    event_types = [event.type for event in events]
    
    # Should have CUSTOM events for artifact
    assert EventType.CUSTOM in event_types, "Missing CUSTOM events"
    
    # Should have TEXT_MESSAGE events for summary
    assert EventType.TEXT_MESSAGE_START in event_types, "Missing TEXT_MESSAGE_START"
    assert EventType.TEXT_MESSAGE_CONTENT in event_types, "Missing TEXT_MESSAGE_CONTENT"
    assert EventType.TEXT_MESSAGE_END in event_types, "Missing TEXT_MESSAGE_END"
    
    # Check custom events
    custom_events = [e for e in events if e.type == EventType.CUSTOM]
    custom_names = [e.name for e in custom_events]
    
    assert "artifact_streaming_start" in custom_names, "Missing artifact_streaming_start"
    assert "artifact_streaming" in custom_names, "Missing artifact_streaming"
    assert "artifact_created" in custom_names, "Missing artifact_created"
    
    # Check text message events come after artifact events
    artifact_created_idx = next(i for i, e in enumerate(events) 
                                if e.type == EventType.CUSTOM and e.name == "artifact_created")
    text_start_idx = next(i for i, e in enumerate(events) 
                         if e.type == EventType.TEXT_MESSAGE_START)
    
    assert text_start_idx > artifact_created_idx, "Summary should come after artifact creation"
    
    print("✓ Two-step process works correctly")
    print(f"  - Step 1: Artifact events ({len(custom_events)} custom events)")
    print(f"  - Step 2: Chat summary (TEXT_MESSAGE events)")


async def test_two_step_artifact_update():
    """Test that canvas agent streams both artifact and summary on update"""
    print("\nTesting two-step artifact update...")
    
    agent = CanvasAgent()
    
    state = {
        "messages": [
            {"role": "user", "content": "Write a hello function"},
            {"role": "assistant", "content": "Created function"},
            {"role": "user", "content": "Add a docstring"}
        ],
        "thread_id": "test",
        "run_id": "test",
        "artifact": {
            "currentIndex": 1,
            "contents": [{
                "index": 1,
                "type": "code",
                "title": "Hello Function",
                "code": "def hello():\n    print('Hello')",
                "language": "python"
            }]
        },
        "selectedText": None,
        "artifactAction": "update"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Check we got the expected events
    event_types = [event.type for event in events]
    
    assert EventType.CUSTOM in event_types, "Missing CUSTOM events"
    assert EventType.TEXT_MESSAGE_START in event_types, "Missing TEXT_MESSAGE_START for summary"
    
    # Check custom events
    custom_events = [e for e in events if e.type == EventType.CUSTOM]
    custom_names = [e.name for e in custom_events]
    
    assert "artifact_updated" in custom_names, "Missing artifact_updated"
    
    print("✓ Two-step update process works correctly")


async def main():
    """Run tests"""
    print("=" * 60)
    print("Canvas Two-Step Process Tests")
    print("=" * 60)
    
    try:
        await test_two_step_artifact_creation()
        await test_two_step_artifact_update()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
