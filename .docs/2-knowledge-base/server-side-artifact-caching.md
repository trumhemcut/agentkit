# Server-Side Artifact Caching

## Overview

Implemented server-side caching for artifacts to eliminate the need for frontends to send full artifact content with every request. Artifacts are stored in memory on the server with unique IDs, allowing clients to reference them by ID alone.

## Key Changes

### 1. New Cache Module (`backend/cache/`)

**Files:**
- `artifact_cache.py` - Main caching implementation
- `__init__.py` - Module exports

**Features:**
- In-memory cache with TTL (24 hours default)
- Thread-based artifact organization
- Automatic expiration cleanup
- Cache statistics tracking
- Full CRUD operations (Create, Read, Update, Delete)

**ArtifactCache API:**
```python
# Store artifact (returns artifact_id)
artifact_id = artifact_cache.store(artifact, thread_id, artifact_id=None)

# Retrieve artifact by ID
artifact = artifact_cache.get(artifact_id)

# Update existing artifact
success = artifact_cache.update(artifact_id, updated_artifact)

# Delete artifact
success = artifact_cache.delete(artifact_id)

# Get all artifacts for a thread
artifacts = artifact_cache.get_thread_artifacts(thread_id)

# Get cache statistics
stats = artifact_cache.get_cache_stats()

# Clear all artifacts
artifact_cache.clear()
```

### 2. Updated API Models (`backend/api/models.py`)

**RunAgentInput:**
```python
artifact: Optional[ArtifactV3] = None  # DEPRECATED
artifact_id: Optional[str] = None      # NEW: Use this instead
```

**CanvasMessageRequest:**
```python
artifact: Optional[ArtifactV3] = None  # DEPRECATED  
artifact_id: Optional[str] = None      # NEW: Use this instead
```

### 3. Updated CanvasAgent (`backend/agents/canvas_agent.py`)

**Key Changes:**
- Imports `artifact_cache` from cache module
- Retrieves artifacts from cache on `run()` entry if `artifact_id` provided
- Generates new `artifact_id` when creating artifacts
- Updates cache after artifact modifications
- Includes `artifact_id` in all event metadata

**Event Metadata Example:**
```python
metadata={
    "message_type": "artifact",
    "artifact_type": "code",
    "artifact_id": "abc-123-def",  # NEW
    "language": "python",
    "title": "Hello World"
}
```

**Methods Updated:**
- `run()` - Retrieves from cache using artifact_id
- `_create_artifact()` - Generates artifact_id and caches result
- `_update_artifact()` - Updates cache after modification
- `_stream_partial_update()` - Updates cache after partial edit

### 4. Updated API Routes (`backend/api/routes.py`)

**Key Changes:**
- Imports `artifact_cache` 
- Prioritizes `artifact_id` over `artifact` field
- Retrieves artifact from cache before passing to agent
- Maintains backward compatibility with full artifact objects

**Route Logic:**
```python
# Handle artifact retrieval: prioritize artifact_id over artifact
artifact = None
if input_data.artifact_id:
    artifact = artifact_cache.get(input_data.artifact_id)
elif input_data.artifact:
    # Legacy: client sent full artifact (deprecated)
    artifact = input_data.artifact.model_dump()
```

**Updated Endpoints:**
- `/chat/{agent_id}` - Unified endpoint with caching support
- `/canvas/stream` - Deprecated endpoint with caching support

## Request/Response Flow

### Creating New Artifact

**Frontend → Backend:**
```json
{
  "messages": [...],
  "action": "create",
  "artifact_id": null
}
```

**Backend → Frontend (via event metadata):**
```json
{
  "metadata": {
    "artifact_id": "new-artifact-123",
    "artifact_type": "code",
    ...
  }
}
```

**What Frontend Should Do:**
- Extract `artifact_id` from metadata
- Store it for subsequent requests
- Don't send full artifact content anymore

### Updating Existing Artifact

**Frontend → Backend:**
```json
{
  "messages": [...],
  "action": "update",
  "artifact_id": "new-artifact-123"  // Only send ID
}
```

**Backend Processing:**
1. Retrieves artifact from cache using ID
2. Applies updates
3. Stores updated artifact back to cache
4. Streams updated content to frontend
5. Includes same `artifact_id` in metadata

## Benefits

1. **Reduced Network Traffic**: Frontend only sends artifact IDs (typically 36 bytes) instead of full content (potentially kilobytes)
2. **Better Performance**: Less data transmission on each request
3. **Simplified Frontend**: No need to manage full artifact state
4. **Automatic Versioning**: Server maintains artifact history
5. **Thread Association**: Artifacts linked to conversation threads

## Backward Compatibility

The implementation maintains full backward compatibility:
- New clients: Send `artifact_id` only (recommended)
- Legacy clients: Can still send full `artifact` object
- Both approaches work seamlessly
- Gradual migration path for frontends

## Configuration

**TTL (Time-to-Live):**
- Default: 24 hours
- Configurable in `artifact_cache.py`
- Artifacts auto-expire after TTL

**Cache Location:**
- In-memory storage (single instance)
- Cleared on server restart
- Future: Can migrate to Redis/database

## Testing

**Test File:** `backend/tests/test_artifact_cache.py`

**Run Tests:**
```bash
cd backend
python tests/test_artifact_cache.py
```

**Test Coverage:**
- Store and retrieve artifacts
- Custom artifact IDs
- Update operations
- Delete operations
- Thread-based retrieval
- Cache clearing
- Statistics tracking
- Multiple versions
- Non-existent artifact handling

## Documentation

**Primary Documentation:** [ARTIFACT_CACHE_README.md](../ARTIFACT_CACHE_README.md)

Covers:
- Detailed architecture
- API reference
- Usage examples
- Migration guide
- Troubleshooting
- Security considerations
- Future enhancements

## Frontend Integration Requirements

To fully leverage server-side caching, frontends need to:

1. **Capture artifact_id from events:**
   ```typescript
   // When receiving TEXT_MESSAGE_START event
   if (event.metadata.message_type === "artifact") {
     const artifactId = event.metadata.artifact_id;
     // Store this for subsequent requests
   }
   ```

2. **Send artifact_id instead of full artifact:**
   ```typescript
   const request = {
     messages: [...],
     artifact_id: artifactId,  // NEW
     // artifact: {...},        // DEPRECATED - don't send this
     action: "update"
   };
   ```

3. **Handle missing artifacts gracefully:**
   - If server can't find artifact (expired/not found), allow re-creation
   - Log warnings but don't fail hard

## Future Enhancements

1. **Persistent Storage**: Migrate from in-memory to Redis/database for durability
2. **Access Control**: Add validation to prevent cross-thread artifact access
3. **Compression**: Compress artifact content to save memory
4. **Distributed Caching**: Support multi-instance deployments
5. **Cleanup Jobs**: Background jobs for expired artifact cleanup
6. **Analytics**: Track cache hit rates and usage patterns
7. **Size Limits**: Implement max cache size with LRU eviction

## Security Considerations

Current implementation:
- No access control validation
- No size limits on cache
- No rate limiting

**TODO:**
- Validate `thread_id` matches user session
- Implement max cache size
- Add rate limiting for cache operations
- Sanitize artifact content

## Monitoring

Get runtime statistics:
```python
from cache.artifact_cache import artifact_cache

stats = artifact_cache.get_cache_stats()
# Returns: {"total_artifacts": N, "threads": M, "expired": K}
```

## Related Files

- `backend/cache/artifact_cache.py` - Cache implementation
- `backend/agents/canvas_agent.py` - Agent integration
- `backend/api/routes.py` - API endpoint integration
- `backend/api/models.py` - Request/response models
- `backend/tests/test_artifact_cache.py` - Test suite
- `backend/ARTIFACT_CACHE_README.md` - Detailed documentation
