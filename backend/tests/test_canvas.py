"""
Test canvas feature implementation
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.canvas_agent import CanvasAgent
from graphs.canvas_graph import CanvasGraphState, detect_intent_node, route_to_handler


async def test_intent_detection():
    """Test intent detection logic"""
    print("Testing intent detection...")
    
    # Test create intent
    state = {
        "messages": [{"role": "user", "content": "Create a Python function"}],
        "thread_id": "test",
        "run_id": "test",
        "artifact": None,
        "selectedText": None,
        "artifactAction": None
    }
    
    result = detect_intent_node(state)
    assert result["artifactAction"] == "create", f"Expected 'create', got {result['artifactAction']}"
    print("✓ Create intent detected correctly")
    
    # Test update intent with existing artifact
    state["artifact"] = {
        "currentIndex": 1,
        "contents": [{
            "index": 1,
            "type": "code",
            "title": "Test",
            "code": "print('hello')",
            "language": "python"
        }]
    }
    state["messages"].append({"role": "user", "content": "Update the function to say goodbye"})
    
    result = detect_intent_node(state)
    assert result["artifactAction"] in ["update", "rewrite"], f"Expected 'update' or 'rewrite', got {result['artifactAction']}"
    print("✓ Update intent detected correctly")
    
    # Test chat only (no keywords)
    state["artifact"] = None
    state["artifactAction"] = None
    state["messages"] = [{"role": "user", "content": "What's the weather like?"}]
    
    result = detect_intent_node(state)
    route = route_to_handler(result)
    assert route == "chat_only", f"Expected 'chat_only', got {route}"
    print("✓ Chat-only intent detected correctly")


async def test_artifact_type_detection():
    """Test artifact type detection"""
    print("\nTesting artifact type detection...")
    
    agent = CanvasAgent()
    
    # Test code detection
    message = "Write a Python function to calculate factorial"
    artifact_type = agent._detect_artifact_type(message)
    assert artifact_type == "code", f"Expected 'code', got {artifact_type}"
    print("✓ Code type detected correctly")
    
    # Test text detection
    message = "Write a blog post about AI"
    artifact_type = agent._detect_artifact_type(message)
    assert artifact_type == "text", f"Expected 'text', got {artifact_type}"
    print("✓ Text type detected correctly")


async def test_language_detection():
    """Test programming language detection"""
    print("\nTesting language detection...")
    
    agent = CanvasAgent()
    
    # Test Python
    message = "Write a Python function"
    code = "def hello():\n    print('hi')"
    lang = agent._detect_language(message, code)
    assert lang == "python", f"Expected 'python', got {lang}"
    print("✓ Python detected correctly")
    
    # Test JavaScript
    message = "Write a JavaScript function"
    code = "function hello() { console.log('hi'); }"
    lang = agent._detect_language(message, code)
    assert lang == "javascript", f"Expected 'javascript', got {lang}"
    print("✓ JavaScript detected correctly")


async def test_title_extraction():
    """Test title extraction from code"""
    print("\nTesting title extraction...")
    
    agent = CanvasAgent()
    
    # Test function title
    code = "def calculate_factorial(n):\n    return 1"
    title = agent._extract_title(code, "code")
    assert "calculate_factorial" in title, f"Expected function name in title, got {title}"
    print(f"✓ Function title extracted: {title}")
    
    # Test class title
    code = "class Calculator:\n    pass"
    title = agent._extract_title(code, "code")
    assert "Calculator" in title, f"Expected class name in title, got {title}"
    print(f"✓ Class title extracted: {title}")
    
    # Test markdown title
    markdown = "# My Document\n\nContent here"
    title = agent._extract_title(markdown, "text")
    assert "My Document" in title, f"Expected heading in title, got {title}"
    print(f"✓ Markdown title extracted: {title}")


async def test_canvas_tools():
    """Test canvas tools"""
    print("\nTesting canvas tools...")
    
    from tools.canvas_tools import ExtractCodeTool, AnalyzeArtifactTool
    
    # Test extract code tool
    artifact = {
        "currentIndex": 1,
        "contents": [{
            "index": 1,
            "type": "code",
            "title": "Test Function",
            "code": "def test():\n    return True",
            "language": "python"
        }]
    }
    
    tool = ExtractCodeTool()
    result = await tool.execute(artifact=artifact)
    assert result["code"] == "def test():\n    return True"
    assert result["language"] == "python"
    print("✓ ExtractCodeTool works correctly")
    
    # Test analyze tool
    analyze_tool = AnalyzeArtifactTool()
    result = await analyze_tool.execute(artifact=artifact)
    assert result["type"] == "code"
    assert result["language"] == "python"
    assert result["has_functions"] == True
    print("✓ AnalyzeArtifactTool works correctly")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Canvas Feature Backend Tests")
    print("=" * 60)
    
    try:
        await test_intent_detection()
        await test_artifact_type_detection()
        await test_language_detection()
        await test_title_extraction()
        await test_canvas_tools()
        
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
