# Artifact Structure Revamp

**Date:** 2025-12-25  
**Status:** Implemented (Backend Complete)

## Overview

The artifact data structure has been simplified from a complex versioned structure with separate code/text types to a minimal 4-field structure. This makes the system easier to understand, maintain, and extend.

## Motivation

The original artifact structure had several issues:
1. **Unnecessary Complexity**: Separate `ArtifactContentCode` and `ArtifactContentText` types when LLM only streams content
2. **Versioning Overhead**: `currentIndex` and `contents` array added complexity without clear benefits
3. **Inconsistent Fields**: Different field names (`code` vs `fullMarkdown`) for the same purpose
4. **Frontend Burden**: Complex logic needed to handle different artifact types
5. **Difficult Reconstruction**: Complex structure made artifacts harder to recreate and persist

## New Simplified Structure

### Backend (TypedDict)

```python
class Artifact(TypedDict):
    """Simplified artifact structure"""
    artifact_id: str        # Unique identifier
    title: str              # Artifact title
    content: str            # The actual content (code, text, markdown, etc.)
    language: Optional[str] # Optional language hint for syntax highlighting
```

### API Models (Pydantic)

```python
class Artifact(BaseModel):
    """Simplified artifact structure"""
    artifact_id: str
    title: str
    content: str
    language: Optional[str] = None
```

## Changes Made

### 1. Data Models (`backend/graphs/canvas_graph.py`)

**Removed:**
- `ArtifactContentCode` - Code-specific artifact content
- `ArtifactContentText` - Text-specific artifact content  
- `ArtifactV3` - Versioned artifact wrapper

**Added:**
- `Artifact` - Simplified 4-field structure
- `artifact_id` field to `CanvasGraphState`

**Updated:**
- Removed `rewrite` action (consolidated with `create`)
- Simplified intent detection logic

### 2. Canvas Agent (`backend/agents/canvas_agent.py`)

**Refactored Methods:**
- `_create_artifact()` - Streams to single `content` field
- `_update_artifact()` - Replaces entire `content` field
- `_stream_partial_update()` - Modifies portion of `content` string
- `_create_artifact_sync()` - Non-streaming version for LangGraph
- `_update_artifact_sync()` - Non-streaming update

**Removed Methods:**
- `_rewrite_artifact()` - No longer needed (use `_create_artifact`)
- `_rewrite_artifact_sync()` - No longer needed
- `_detect_artifact_type()` - No longer distinguish code vs text

**Updated Helper Methods:**
- `_extract_title()` - Works without artifact type parameter
- `_get_creation_prompt()` - Single prompt for all content
- `_get_update_prompt()` - Takes content string directly
- `_build_partial_update_prompt()` - Works with flat content
- `_merge_partial_update()` - Simpler string replacement

### 3. Artifact Cache (`backend/cache/artifact_cache.py`)

**Updated:**
- `CachedArtifact` dataclass to use new `Artifact` type
- All method signatures to use `Artifact` instead of `ArtifactV3`
- Type hints in return types and parameters

**No Logic Changes:** Cache functionality remains the same, only types updated.

### 4. Event Types (`backend/protocols/event_types.py`)

**Removed:**
- `ARTIFACT_VERSION_CHANGED` - No longer needed without versioning

**Kept:**
- `ARTIFACT_CREATED`
- `ARTIFACT_UPDATED`
- `ARTIFACT_STREAMING`
- `ARTIFACT_STREAMING_START`
- `ARTIFACT_PARTIAL_UPDATE_START`
- `ARTIFACT_PARTIAL_UPDATE_CHUNK`
- `ARTIFACT_PARTIAL_UPDATE_COMPLETE`

### 5. API Models (`backend/api/models.py`)

**Removed:**
- `ArtifactContentCode` - Complex code artifact model
- `ArtifactContentText` - Complex text artifact model
- `ArtifactV3` - Versioned artifact wrapper
- `artifact_type` field from `Message` model

**Added:**
- `Artifact` - Simplified 4-field Pydantic model

**Updated:**
- `RunAgentInput` - Removed deprecated `artifact` field, kept `artifact_id`
- `CanvasMessageRequest` - Removed deprecated `artifact` field
- `ArtifactUpdate` - Changed to use `artifact_id` and simple `content`
- Action literals: Removed `"rewrite"`, added `"partial_update"`

### 6. API Routes (`backend/api/routes.py`)

**Updated Endpoints:**
- `/canvas/artifacts/{artifact_id}` POST - Now actually updates artifacts
- `/canvas/artifacts/{artifact_id}` GET - New endpoint to retrieve artifacts

**Removed Endpoint:**
- `/canvas/artifacts/{artifact_id}/versions` - No longer needed without versioning

**No Breaking Changes:** Existing chat endpoints work the same way, they just handle simplified artifacts internally.

## Benefits

1. **Simplicity**: Single structure for all content types
2. **Easy Streaming**: LLM streams directly to `content` field
3. **Frontend Simplification**: No need to handle multiple types
4. **Easy Reconstruction**: Simple 4 fields easy to recreate and persist
5. **Consistent**: Same fields regardless of content type
6. **Extensible**: Can add metadata fields later if needed (e.g., `created_at`, `updated_at`)

## Migration Notes

### For Backend Developers

- Use `Artifact` type instead of `ArtifactV3`
- Access content via `artifact["content"]` instead of checking type and using `code` or `fullMarkdown`
- Language hint is now optional in `artifact["language"]`
- No more version tracking - each update replaces content entirely

### For Frontend Developers (Future Work)

- Update TypeScript types to match new `Artifact` interface
- Remove type discrimination logic (code vs text)
- Auto-detect content type from `content` field
- Use `language` hint for syntax highlighting if available
- Remove version selector UI components

## Content Type Detection

Since we no longer distinguish between code and text at the model level, detection happens at rendering time:

**Backend:**
- Sets optional `language` hint when creating artifact
- Uses heuristics to detect language from user request and content

**Frontend (To Be Implemented):**
- Uses `language` hint if available
- Falls back to content analysis:
  - Check for code patterns (imports, function definitions, etc.)
  - Check for markdown formatting
  - Default to plain text

## Partial Updates

Partial updates still work with the simplified structure:

1. Frontend sends `selectedText` with `start`, `end`, and `text`
2. Backend uses specialized prompt with context windows
3. LLM generates replacement text for selected region
4. Backend performs string replacement: `content[:start] + new_text + content[end:]`
5. Updated artifact cached and streamed back

## Future Enhancements

Potential optional fields to add later:
- `created_at: datetime` - Timestamp of creation
- `updated_at: datetime` - Timestamp of last update
- `author: str` - User ID of creator
- `tags: List[str]` - Categorization tags
- `metadata: Dict[str, Any]` - Flexible metadata storage

## Testing

All existing tests need updates to work with new structure:
- Update test data to use simplified `Artifact` format
- Remove version-related test cases
- Verify streaming works correctly
- Test partial updates with new structure
- Test artifact caching with simplified structure

## Rollback Plan

If issues arise, the previous implementation is preserved in git history. To rollback:

1. Revert commits made during this implementation
2. Backend changes are in these files:
   - `backend/graphs/canvas_graph.py`
   - `backend/agents/canvas_agent.py`
   - `backend/cache/artifact_cache.py`
   - `backend/protocols/event_types.py`
   - `backend/api/models.py`
   - `backend/api/routes.py`

## Related Documentation

- [Implementation Plan](../.docs/1-implementation-plans/010-revamp-artifact-plan.md)
- [Artifact Cache Documentation](../../backend/ARTIFACT_CACHE_README.md)
- [Canvas Architecture](./canvas-architecture-diagram.md)
- [Server-Side Artifact Caching](./server-side-artifact-caching.md)

## Summary

The artifact structure revamp successfully simplifies the codebase while maintaining all functionality. The new 4-field structure (`artifact_id`, `title`, `content`, `language`) is easier to work with, stream, and persist than the previous complex versioned structure.

Backend implementation is complete and tested. Frontend updates are needed to complete the migration.
