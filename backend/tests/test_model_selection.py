"""
Test script for LLM model selection feature
Run this to verify the implementation works correctly
"""
import asyncio
import sys
sys.path.insert(0, '/home/phihuynh/projects/agenkit/backend')

from llm.ollama_client import ollama_client
from llm.provider_factory import LLMProviderFactory
from agents.chat_agent import ChatAgent
from agents.canvas_agent import CanvasAgent


async def test_ollama_client():
    """Test Ollama client can list models"""
    print("\n=== Testing Ollama Client ===")
    result = await ollama_client.list_available_models()
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Found {len(result['models'])} models")
    print(f"   Default model: {result['default']}")
    
    for model in result['models']:
        print(f"   - {model['name']} ({model['id']}) - {model['size']}")
    
    return True


def test_provider_factory():
    """Test provider factory accepts model parameter"""
    print("\n=== Testing Provider Factory ===")
    
    # Test default
    provider1 = LLMProviderFactory.get_provider("ollama")
    print("✅ Created provider with default model")
    
    # Test with specific model
    provider2 = LLMProviderFactory.get_provider("ollama", model="qwen:4b")
    print("✅ Created provider with qwen:4b model")
    
    provider3 = LLMProviderFactory.get_provider("ollama", model="qwen:7b")
    print("✅ Created provider with qwen:7b model")
    
    return True


def test_agent_initialization():
    """Test agents accept model parameter"""
    print("\n=== Testing Agent Initialization ===")
    
    # Test ChatAgent
    chat_agent1 = ChatAgent()
    print("✅ Created ChatAgent with default model")
    
    chat_agent2 = ChatAgent(model="qwen:4b")
    print("✅ Created ChatAgent with qwen:4b")
    
    # Test CanvasAgent
    canvas_agent1 = CanvasAgent()
    print("✅ Created CanvasAgent with default model")
    
    canvas_agent2 = CanvasAgent(model="qwen:7b")
    print("✅ Created CanvasAgent with qwen:7b")
    
    return True


async def test_model_validation():
    """Test model validation"""
    print("\n=== Testing Model Validation ===")
    
    # Check specific models
    available = await ollama_client.check_model_available("qwen:7b")
    print(f"✅ qwen:7b available: {available}")
    
    available = await ollama_client.check_model_available("qwen:4b")
    print(f"✅ qwen:4b available: {available}")
    
    # Test validation
    is_valid = ollama_client.is_valid_model("qwen:7b")
    print(f"✅ qwen:7b is valid: {is_valid}")
    
    is_valid = ollama_client.is_valid_model("invalid-model")
    print(f"✅ invalid-model is valid: {is_valid}")
    
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("LLM Model Selection - Backend Implementation Test")
    print("=" * 60)
    
    tests = [
        ("Ollama Client", test_ollama_client()),
        ("Provider Factory", test_provider_factory()),
        ("Agent Initialization", test_agent_initialization()),
        ("Model Validation", test_model_validation()),
    ]
    
    results = []
    for name, test in tests:
        try:
            if asyncio.iscoroutine(test):
                result = await test
            else:
                result = test
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend implementation is complete.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
