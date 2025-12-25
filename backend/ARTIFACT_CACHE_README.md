# Server-Side Artifact Caching

## Overview

Server-side artifact caching eliminates the need for the frontend to send full artifact content with every request. Instead, artifacts are cached on the server with unique IDs, and the frontend only needs to send the `artifact_id` to reference the cached artifact.

## Benefits

- **Reduced Network Traffic**: Frontend only sends artifact IDs instead of full content
- **Improved Performance**: Less data transmission on each request
- **Simpler Frontend Logic**: Frontend doesn't need to manage full artifact state
- **Version Control**: Server maintains artifact versions automatically
- **Thread Association**: Artifacts are associated with conversation threads

## Architecture

### Cache Module

Location: `backend/cache/artifact_cache.py`

The `ArtifactCache` class provides:
- **In-memory storage** with TTL (24 hours default)
- **Thread-based organization** for conversation context
- **Automatic cleanup** of expired artifacts
- **Statistics tracking** for monitoring

### Key Components

1. **ArtifactCache Class**
   - `store(artifact, thread_id, artifact_id=None)`: Store/update artifact
   - `get(artifact_id)`: Retrieve artifact by ID
   - `update(artifact_id, artifact)`: Update existing artifact
   - `delete(artifact_id)`: Remove artifact from cache
   - `get_thread_artifacts(thread_id)`: Get all artifacts for a thread
   - `clear()`: Clear entire cache
   - `get_cache_stats()`: Get cache statistics

2. **Global Instance**
   - Singleton `artifact_cache` instance available throughout backend
   - Configured with 24-hour TTL by default

## API Changes

### Request Models

Both `RunAgentInput` and `CanvasMessageRequest` now support:

```python
class RunAgentInput(BaseModel):
    # ... existing fields ...
    artifact: Optional[ArtifactV3] = None  # DEPRECATED
    artifact_id: Optional[str] = None      # NEW: Use this instead
```

- `artifact`: Legacy field, still supported but deprecated
- `artifact_id`: New field for referencing cached artifacts

### Response Events

The `TextMessageStartEvent` metadata now includes `artifact_id`:

```json
{
  "type": "TEXT_MESSAGE_START",
  "message_id": "...",
  "role": "assistant",
  "metadata": {
    "message_type": "artifact",
    "artifact_type": "code",
    "artifact_id": "abc-123-def",  // NEW: Frontend caches this
    "language": "python",
    "title": "..."
  }
}
```

## Usage Flow

### 1. Creating New Artifact

**Frontend → Backend:**
```json
{
  "messages": [...],
  "action": "create",
  "artifact_id": null  // No artifact yet
}
```

**Backend → Frontend (in metadata):**
```json
{
  "metadata": {
    "artifact_id": "new-artifact-123"  // Frontend stores this
  }
}
```

### 2. Updating Existing Artifact

**Frontend → Backend:**
```json
{
  "messages": [...],
  "action": "update",
  "artifact_id": "new-artifact-123"  // Reference only
  // No need to send full artifact content!
}
```

**Backend:**
- Retrieves artifact from cache using `artifact_id`
- Updates the artifact
- Stores updated version back to cache
- Returns new artifact content with same `artifact_id`

### 3. Partial Updates

**Frontend → Backend:**
```json
{
  "messages": [...],
  "artifact_id": "new-artifact-123",
  "selectedText": {
    "start": 0,
    "end": 10,
    "text": "selected"
  }
}
```

**Backend:**
- Retrieves artifact from cache
- Applies partial update
- Updates cache with new version

## Integration Points

### Canvas Agent (`backend/agents/canvas_agent.py`)

The CanvasAgent handles artifact caching automatically:

1. **On `run()` method entry**: Retrieves artifact from cache if `artifact_id` provided
2. **On artifact creation**: Generates new `artifact_id` and caches artifact
3. **On artifact update**: Updates cached artifact with new version
4. **In all events**: Includes `artifact_id` in metadata

### API Routes (`backend/api/routes.py`)

The routes handle cache retrieval:

```python
# Prioritize artifact_id over artifact
artifact = None
if input_data.artifact_id:
    artifact = artifact_cache.get(input_data.artifact_id)
elif input_data.artifact:
    # Legacy support
    artifact = input_data.artifact.model_dump()
```

## Configuration

### TTL (Time-to-Live)

Default: 24 hours

Modify in `backend/cache/artifact_cache.py`:

```python
artifact_cache = ArtifactCache(ttl_hours=24)
```

### Cache Size

Currently unlimited (in-memory). For production:
- Consider implementing LRU eviction
- Add max cache size limit
- Use persistent storage (Redis, etc.)

## Testing

Run artifact cache tests:

```bash
cd backend
python -m pytest tests/test_artifact_cache.py -v
```

## Migration Guide

### Frontend Changes Required

1. **Store artifact_id from metadata:**
   ```typescript
   // When receiving TEXT_MESSAGE_START event
   const artifactId = event.metadata.artifact_id;
   // Store this for subsequent requests
   ```

2. **Send artifact_id instead of full artifact:**
   ```typescript
   // OLD (deprecated)
   const request = {
     messages: [...],
     artifact: fullArtifactObject,
     action: "update"
   };
   
   // NEW (recommended)
   const request = {
     messages: [...],
     artifact_id: artifactId,
     action: "update"
   };
   ```

3. **Still receive full content in responses:**
   - Frontend still receives streamed artifact content
   - Only the request payload is simplified

### Backward Compatibility

The backend supports both approaches:
- New clients: Send `artifact_id` only
- Legacy clients: Can still send full `artifact` object
- Both work seamlessly

## Future Enhancements

1. **Persistent Storage**: Move from in-memory to Redis/database
2. **Cache Analytics**: Track hit rates, popular artifacts
3. **Compression**: Compress artifact content to save memory
4. **Distributed Caching**: Support multi-instance deployments
5. **Versioning API**: Expose endpoints to browse artifact history
6. **Cleanup Jobs**: Background jobs for expired artifact cleanup

## Monitoring

Get cache statistics:

```python
from cache.artifact_cache import artifact_cache

stats = artifact_cache.get_cache_stats()
print(f"Total artifacts: {stats['total_artifacts']}")
print(f"Threads: {stats['threads']}")
print(f"Expired: {stats['expired']}")
```

## Security Considerations

1. **Access Control**: Currently no validation that user owns artifact
   - TODO: Add thread_id validation to prevent cross-thread access
   
2. **Cache Poisoning**: Validate artifact structure on retrieval
   
3. **Memory Limits**: Implement max cache size to prevent OOM

## Troubleshooting

### Artifact not found in cache

**Symptoms**: Warning log `"Artifact ID provided but not found in cache"`

**Causes**:
- Artifact expired (> 24 hours)
- Server restarted (in-memory cache cleared)
- Invalid artifact_id

**Solution**: Frontend should handle this gracefully and allow artifact re-creation

### Cache growing too large

**Solution**: Reduce TTL or implement LRU eviction:
```python
artifact_cache = ArtifactCache(ttl_hours=12)  # Reduce TTL
```

## Example Code

### Caching an Artifact

```python
from cache.artifact_cache import artifact_cache

artifact = {
    "currentIndex": 1,
    "contents": [...]
}

artifact_id = artifact_cache.store(
    artifact=artifact,
    thread_id="thread-123"
)
```

### Retrieving an Artifact

```python
artifact = artifact_cache.get("artifact-id-123")
if artifact:
    print(f"Found artifact with {len(artifact['contents'])} versions")
else:
    print("Artifact not found or expired")
```

### Updating an Artifact

```python
# Get current artifact
artifact = artifact_cache.get("artifact-id-123")

# Modify it
artifact["currentIndex"] = 2
artifact["contents"].append(new_version)

# Update cache
artifact_cache.update("artifact-id-123", artifact)
```
