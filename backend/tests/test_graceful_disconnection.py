"""
Test script to verify graceful disconnection handling when clients abort streaming.

This script tests that:
1. FastAPI's StreamingResponse handles client disconnections gracefully
2. GeneratorExit exceptions are caught and logged properly
3. Backend resources are cleaned up correctly

Usage:
    python backend/tests/test_graceful_disconnection.py
"""

import asyncio
import logging
import sys
from pathlib import Path
import httpx

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend URL
BASE_URL = "http://localhost:8000"


async def test_client_abort_during_streaming():
    """Test that client can abort streaming and backend handles it gracefully"""
    
    # Prepare test request
    test_request = {
        "thread_id": "test-thread-abort",
        "run_id": "test-run-abort",
        "messages": [
            {"role": "user", "content": "Write a very long story about AI agents"}
        ],
        "agent": "chat"
    }
    
    logger.info("Starting streaming request...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream("POST", f"{BASE_URL}/api/chat/chat", json=test_request) as response:
                logger.info(f"Response status: {response.status_code}")
                
                # Read a few chunks
                chunk_count = 0
                async for chunk in response.aiter_bytes():
                    chunk_count += 1
                    logger.info(f"Received chunk {chunk_count}: {len(chunk)} bytes")
                    
                    # Abort after 3 chunks (simulates user clicking Stop button)
                    if chunk_count >= 3:
                        logger.info("Simulating client abort (user clicked Stop button)...")
                        break
                
                # Connection will be closed when exiting context manager
                logger.info("Connection closed by client")
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error (expected when aborting): {e}")
    
    logger.info("✅ Test completed - backend should log 'Client disconnected'")
    logger.info("Check backend logs for '[ROUTES] Client disconnected' message")


async def test_abort_during_a2ui_action():
    """Test that client can abort during A2UI action processing"""
    
    # Prepare test request
    test_request = {
        "userAction": {
            "name": "test_action",
            "surfaceId": "test-surface",
            "sourceComponentId": "test-component",
            "timestamp": "2026-01-03T10:00:00Z",
            "context": {}
        },
        "threadId": "test-thread-action-abort",
        "runId": "test-run-action-abort"
    }
    
    logger.info("Starting A2UI action request...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream("POST", f"{BASE_URL}/api/agents/a2ui-loop/action", json=test_request) as response:
                logger.info(f"Response status: {response.status_code}")
                
                # Read a few chunks and abort
                chunk_count = 0
                async for chunk in response.aiter_bytes():
                    chunk_count += 1
                    logger.info(f"Received chunk {chunk_count}: {len(chunk)} bytes")
                    
                    if chunk_count >= 2:
                        logger.info("Aborting A2UI action processing...")
                        break
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error (expected when aborting): {e}")
    
    logger.info("✅ A2UI action test completed")


async def test_normal_completion():
    """Test that normal completion still works (no abort)"""
    
    test_request = {
        "thread_id": "test-thread-complete",
        "run_id": "test-run-complete",
        "messages": [
            {"role": "user", "content": "Say hello"}
        ],
        "agent": "chat"
    }
    
    logger.info("Testing normal completion (no abort)...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", f"{BASE_URL}/api/chat/chat", json=test_request) as response:
            chunk_count = 0
            async for chunk in response.aiter_bytes():
                chunk_count += 1
            
            logger.info(f"✅ Normal completion - received {chunk_count} chunks")


async def main():
    logger.info("=" * 60)
    logger.info("Testing Graceful Disconnection Handling")
    logger.info("=" * 60)
    logger.info(f"Backend URL: {BASE_URL}")
    logger.info("NOTE: Backend must be running for these tests to work!")
    logger.info("      Start with: uvicorn main:app --reload")
    logger.info("=" * 60)
    
    try:
        logger.info("\n[Test 1] Client abort during streaming")
        await test_client_abort_during_streaming()
        await asyncio.sleep(1)
        
        logger.info("\n[Test 2] Client abort during A2UI action")
        await test_abort_during_a2ui_action()
        await asyncio.sleep(1)
        
        logger.info("\n[Test 3] Normal completion (baseline)")
        await test_normal_completion()
        
        logger.info("\n" + "=" * 60)
        logger.info("All tests completed!")
        logger.info("=" * 60)
        logger.info("\nExpected backend log output:")
        logger.info("  - '[ROUTES] Client disconnected' messages for aborted requests")
        logger.info("  - No errors or exceptions")
        logger.info("  - Clean shutdown for all requests")
        
    except httpx.ConnectError:
        logger.error("\n❌ Cannot connect to backend!")
        logger.error("   Make sure backend is running: uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
