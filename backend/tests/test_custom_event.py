"""
Test CustomEvent structure matches ag-ui protocol
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ag_ui.core import EventType, CustomEvent


async def test_custom_event_structure():
    """Test that CustomEvent is created correctly"""
    print("Testing CustomEvent structure...")
    
    # Create a thinking event
    event = CustomEvent(
        type=EventType.CUSTOM,
        name="thinking",
        value={"message": "Processing create request..."}
    )
    
    assert event.type == EventType.CUSTOM
    assert event.name == "thinking"
    assert event.value == {"message": "Processing create request..."}
    print("✓ CustomEvent structure is correct")
    
    # Create an artifact_created event
    event2 = CustomEvent(
        type=EventType.CUSTOM,
        name="artifact_created",
        value={
            "artifact": {
                "currentIndex": 1,
                "contents": [{
                    "index": 1,
                    "type": "code",
                    "title": "Test",
                    "code": "print('hello')",
                    "language": "python"
                }]
            }
        }
    )
    
    assert event2.type == EventType.CUSTOM
    assert event2.name == "artifact_created"
    assert "artifact" in event2.value
    print("✓ CustomEvent with artifact data is correct")


async def main():
    """Run tests"""
    print("=" * 60)
    print("CustomEvent Structure Tests")
    print("=" * 60)
    
    try:
        await test_custom_event_structure()
        
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
