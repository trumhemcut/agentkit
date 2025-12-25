"""
Tests for server-side artifact caching functionality
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cache.artifact_cache import ArtifactCache
from graphs.canvas_graph import ArtifactV3, ArtifactContentCode, ArtifactContentText


def create_cache():
    """Create a fresh cache instance for testing"""
    return ArtifactCache(ttl_hours=1)


def sample_code_artifact():
    """Sample code artifact"""
    return {
        "currentIndex": 1,
        "contents": [
            {
                "index": 1,
                "type": "code",
                "title": "Hello World",
                "code": "print('Hello, World!')",
                "language": "python"
            }
        ]
    }


def sample_text_artifact():
    """Sample text artifact"""
    return {
        "currentIndex": 1,
        "contents": [
            {
                "index": 1,
                "type": "text",
                "title": "Documentation",
                "fullMarkdown": "# Title\n\nThis is a document."
            }
        ]
    }


def test_store_and_retrieve_artifact():
    """Test storing and retrieving an artifact"""
    print("Testing store and retrieve...")
    cache = create_cache()
    artifact = sample_code_artifact()
    thread_id = "thread-123"
    
    # Store artifact
    artifact_id = cache.store(artifact, thread_id)
    
    assert artifact_id is not None
    assert isinstance(artifact_id, str)
    
    # Retrieve artifact
    retrieved = cache.get(artifact_id)
    
    assert retrieved is not None
    assert retrieved == artifact
    assert retrieved["currentIndex"] == 1
    assert retrieved["contents"][0]["code"] == "print('Hello, World!')"
    print("✓ Store and retrieve works correctly")


def test_store_with_custom_id():
    """Test storing artifact with custom ID"""
    print("Testing store with custom ID...")
    cache = create_cache()
    artifact = sample_code_artifact()
    thread_id = "thread-123"
    custom_id = "custom-artifact-id"
    
    # Store with custom ID
    artifact_id = cache.store(artifact, thread_id, artifact_id=custom_id)
    
    assert artifact_id == custom_id
    
    # Retrieve using custom ID
    retrieved = cache.get(custom_id)
    assert retrieved is not None
    print("✓ Custom ID storage works correctly")


def test_update_artifact():
    """Test updating an existing artifact"""
    print("Testing artifact update...")
    cache = create_cache()
    artifact = sample_code_artifact()
    thread_id = "thread-123"
    
    # Store initial artifact
    artifact_id = cache.store(artifact, thread_id)
    
    # Update artifact
    updated_artifact = {
        "currentIndex": 2,
        "contents": [
            artifact["contents"][0],
            {
                "index": 2,
                "type": "code",
                "title": "Hello World v2",
                "code": "print('Hello, Updated World!')",
                "language": "python"
            }
        ]
    }
    
    success = cache.update(artifact_id, updated_artifact)
    assert success is True
    
    # Retrieve and verify update
    retrieved = cache.get(artifact_id)
    assert retrieved["currentIndex"] == 2
    assert len(retrieved["contents"]) == 2
    assert retrieved["contents"][1]["code"] == "print('Hello, Updated World!')"
    print("✓ Artifact update works correctly")


def test_update_nonexistent_artifact():
    """Test updating artifact that doesn't exist"""
    print("Testing update of nonexistent artifact...")
    cache = create_cache()
    success = cache.update("nonexistent-id", {"currentIndex": 1, "contents": []})
    assert success is False
    print("✓ Update nonexistent returns False as expected")


def test_delete_artifact():
    """Test deleting an artifact"""
    print("Testing artifact deletion...")
    cache = create_cache()
    artifact = sample_code_artifact()
    thread_id = "thread-123"
    
    # Store artifact
    artifact_id = cache.store(artifact, thread_id)
    
    # Verify it exists
    assert cache.get(artifact_id) is not None
    
    # Delete artifact
    success = cache.delete(artifact_id)
    assert success is True
    
    # Verify it's gone
    assert cache.get(artifact_id) is None
    print("✓ Artifact deletion works correctly")


def test_delete_nonexistent_artifact():
    """Test deleting artifact that doesn't exist"""
    print("Testing delete of nonexistent artifact...")
    cache = create_cache()
    success = cache.delete("nonexistent-id")
    assert success is False
    print("✓ Delete nonexistent returns False as expected")


def test_get_thread_artifacts():
    """Test retrieving all artifacts for a thread"""
    print("Testing thread artifact retrieval...")
    cache = create_cache()
    code_artifact = sample_code_artifact()
    text_artifact = sample_text_artifact()
    thread_id = "thread-123"
    other_thread_id = "thread-456"
    
    # Store artifacts in same thread
    artifact_id1 = cache.store(code_artifact, thread_id)
    artifact_id2 = cache.store(text_artifact, thread_id)
    
    # Store artifact in different thread
    artifact_id3 = cache.store(code_artifact, other_thread_id)
    
    # Get artifacts for thread-123
    thread_artifacts = cache.get_thread_artifacts(thread_id)
    
    assert len(thread_artifacts) == 2
    assert artifact_id1 in thread_artifacts
    assert artifact_id2 in thread_artifacts
    assert artifact_id3 not in thread_artifacts
    print("✓ Thread artifact retrieval works correctly")


def test_clear_cache():
    """Test clearing all artifacts"""
    print("Testing cache clear...")
    cache = create_cache()
    artifact = sample_code_artifact()
    thread_id = "thread-123"
    
    # Store multiple artifacts
    artifact_id1 = cache.store(artifact, thread_id)
    artifact_id2 = cache.store(artifact, thread_id)
    
    # Clear cache
    cache.clear()
    
    # Verify all gone
    assert cache.get(artifact_id1) is None
    assert cache.get(artifact_id2) is None
    print("✓ Cache clear works correctly")


def test_cache_stats():
    """Test cache statistics"""
    print("Testing cache statistics...")
    cache = create_cache()
    code_artifact = sample_code_artifact()
    text_artifact = sample_text_artifact()
    thread_id1 = "thread-123"
    thread_id2 = "thread-456"
    
    # Initially empty
    stats = cache.get_cache_stats()
    assert stats["total_artifacts"] == 0
    assert stats["threads"] == 0
    
    # Store artifacts
    cache.store(code_artifact, thread_id1)
    cache.store(text_artifact, thread_id1)
    cache.store(code_artifact, thread_id2)
    
    # Check stats
    stats = cache.get_cache_stats()
    assert stats["total_artifacts"] == 3
    assert stats["threads"] == 2
    print("✓ Cache statistics work correctly")


def test_get_nonexistent_artifact():
    """Test retrieving artifact that doesn't exist"""
    print("Testing get nonexistent artifact...")
    cache = create_cache()
    retrieved = cache.get("nonexistent-id")
    assert retrieved is None
    print("✓ Get nonexistent returns None as expected")


def test_multiple_versions_in_artifact():
    """Test artifact with multiple versions"""
    print("Testing artifact with multiple versions...")
    cache = create_cache()
    thread_id = "thread-123"
    
    artifact = {
        "currentIndex": 3,
        "contents": [
            {
                "index": 1,
                "type": "code",
                "title": "Version 1",
                "code": "print('v1')",
                "language": "python"
            },
            {
                "index": 2,
                "type": "code",
                "title": "Version 2",
                "code": "print('v2')",
                "language": "python"
            },
            {
                "index": 3,
                "type": "code",
                "title": "Version 3",
                "code": "print('v3')",
                "language": "python"
            }
        ]
    }
    
    artifact_id = cache.store(artifact, thread_id)
    retrieved = cache.get(artifact_id)
    
    assert retrieved["currentIndex"] == 3
    assert len(retrieved["contents"]) == 3
    assert retrieved["contents"][2]["code"] == "print('v3')"
    print("✓ Multiple versions work correctly")


if __name__ == "__main__":
    print("\n=== Running Artifact Cache Tests ===\n")
    
    try:
        test_store_and_retrieve_artifact()
        test_store_with_custom_id()
        test_update_artifact()
        test_update_nonexistent_artifact()
        test_delete_artifact()
        test_delete_nonexistent_artifact()
        test_get_thread_artifacts()
        test_clear_cache()
        test_cache_stats()
        test_get_nonexistent_artifact()
        test_multiple_versions_in_artifact()
        
        print("\n=== All Tests Passed! ===\n")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
