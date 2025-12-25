# Implementation Plan: Revamp Artifact Structure

**Status:** Draft  
**Created:** 2025-12-25  
**Requirement:** [010-revamp-artifact.md](../.docs/0-requirements/010-revamp-artifact.md)

## Executive Summary

Simplify the Artifact data structure by removing the distinction between code and text types. Since the LLM only streams content, the artifact should only contain three essential fields: `artifact_id`, `title`, and `content`. This will make it easier to reconstruct artifacts from the frontend and reduce unnecessary complexity.

## Current State Analysis

### Current Artifact Structure (Complex)

**Backend** (`backend/graphs/canvas_graph.py`):
```python
class ArtifactContentCode(TypedDict):
    index: int
    type: Literal["code"]
    title: str
    code: str
    language: str

class ArtifactContentText(TypedDict):
    index: int
    type: Literal["text"]
    title: str
    fullMarkdown: str

class ArtifactV3(TypedDict):
    currentIndex: int
    contents: List[Union[ArtifactContentCode, ArtifactContentText]]
```

**Frontend** (`frontend/types/canvas.ts`):
```typescript
export interface ArtifactContentCode {
  index: number
  type: "code"
  title: string
  code: string
  language: string
}

export interface ArtifactContentText {
  index: number
  type: "text"
  title: string
  fullMarkdown: string
}

export type ArtifactContent = ArtifactContentCode | ArtifactContentText

export interface ArtifactV3 {
  currentIndex: number
  contents: ArtifactContent[]
  artifact_id?: string
}
```

### Issues with Current Implementation

1. **Unnecessary Complexity**: Separate code and text types when LLM only streams content
2. **Versioning Overhead**: `currentIndex` and `contents` array for managing versions adds complexity
3. **Inconsistent Fields**: Different field names (`code` vs `fullMarkdown`) for the same purpose (content)
4. **Frontend Burden**: Frontend needs complex logic to handle different artifact types
5. **Difficult to Recreate**: Complex structure makes it harder to reconstruct artifacts

## Proposed Solution

### New Simplified Artifact Structure

**Backend** (`backend/graphs/canvas_graph.py`):
```python
class Artifact(TypedDict):
    """Simplified artifact structure"""
    artifact_id: str        # Unique identifier
    title: str              # Artifact title
    content: str            # The actual content (code, text, markdown, etc.)
```

**Frontend** (`frontend/types/canvas.ts`):
```typescript
export interface Artifact {
  artifact_id: string
  title: string
  content: string
}
```

### Benefits

1. **Simplicity**: Single structure for all content types
2. **Easy Streaming**: LLM can stream directly to `content` field
3. **Frontend Simplification**: No need to handle multiple types
4. **Easy Reconstruction**: Simple structure is easy to recreate and persist
5. **Consistent**: Same fields regardless of content type
6. **Extensible**: Can add metadata fields later if needed

## Implementation Plan

### Phase 1: Backend Changes

#### 1.1 Update Data Models
**File:** `backend/graphs/canvas_graph.py`

- [ ] Remove `ArtifactContentCode` and `ArtifactContentText` classes
- [ ] Remove `ArtifactV3` class
- [ ] Create new simplified `Artifact` class with `artifact_id`, `title`, `content`
- [ ] Update `CanvasGraphState` to use new `Artifact` type
- [ ] Remove `artifactAction` field or simplify to just "create" and "update"
- [ ] Remove `SelectedText` class (if no longer needed for partial updates, or adapt to new structure)

**Impact:** This is the core data structure change that affects all other components.

#### 1.2 Update Canvas Agent
**File:** `backend/agents/canvas_agent.py`

- [ ] Update all methods to work with simplified `Artifact` structure:
  - `_create_artifact()` - stream to single `content` field
  - `_update_artifact()` - append/modify `content` field
  - `_rewrite_artifact()` - replace `content` field
  - `_stream_partial_update()` - modify portion of `content` field
- [ ] Update prompt engineering to generate simple content stream
- [ ] Remove logic for handling different artifact types (code vs text)
- [ ] Update artifact caching to use simplified structure
- [ ] Simplify event emission (no need for version/index events)

**Impact:** Core agent logic needs refactoring for streaming behavior.

#### 1.3 Update Artifact Cache
**File:** `backend/cache/artifact_cache.py`

- [ ] Update `CachedArtifact` dataclass to use new `Artifact` type
- [ ] Ensure `store()` and `get()` methods work with simplified structure
- [ ] Update any serialization/deserialization logic
- [ ] Remove any version tracking if present

**Impact:** Minimal changes, mainly type updates.

#### 1.4 Update Event Types & Protocols
**File:** `backend/protocols/event_types.py`

- [ ] Review canvas event types - keep only essential ones:
  - `ARTIFACT_CREATED`
  - `ARTIFACT_UPDATED`
  - `ARTIFACT_STREAMING` (for content streaming)
- [ ] Consider removing version-related events:
  - `ARTIFACT_VERSION_CHANGED` (no longer needed)
  - Partial update events (simplify to regular streaming)

**Impact:** Reduces event complexity, may affect frontend event handling.

#### 1.5 Update API Routes
**File:** `backend/api/routes.py`

- [ ] Update request/response models to use simplified `Artifact`
- [ ] Ensure `/canvas/stream` endpoint works with new structure
- [ ] Update any validation logic
- [ ] Test artifact creation and update flows

**Impact:** Minimal changes, mainly type updates in request/response models.

#### 1.6 Update API Models
**File:** `backend/api/models.py`

- [ ] Update Pydantic models for canvas requests to use simplified structure
- [ ] Remove code/text type discrimination in models
- [ ] Simplify `CanvasMessage` model

**Impact:** Pydantic model simplification.

### Phase 2: Frontend Changes

#### 2.1 Update TypeScript Types
**File:** `frontend/types/canvas.ts`

- [ ] Remove `ArtifactContentCode` and `ArtifactContentText` interfaces
- [ ] Remove `ArtifactContent` union type
- [ ] Remove `ArtifactV3` interface
- [ ] Create new simplified `Artifact` interface
- [ ] Update `CanvasMessage` to use new `Artifact` type
- [ ] Update `CanvasEventData` to remove unnecessary fields
- [ ] Remove version-related types

**Impact:** Core type definitions that affect all frontend components.

#### 2.2 Update AG-UI Client
**File:** `frontend/services/agui-client.ts`

- [ ] Update event handlers to process simplified artifact structure
- [ ] Remove handling for version change events
- [ ] Simplify artifact streaming logic
- [ ] Update state management to work with single `content` field

**Impact:** Simplifies event processing logic.

#### 2.3 Update Artifact Components
**Files:** 
- `frontend/components/ArtifactPanel.tsx`
- `frontend/components/Canvas/CodeRenderer.tsx`
- `frontend/components/Canvas/TextRenderer.tsx`

- [ ] Update `ArtifactPanel` to display simplified artifact
- [ ] Simplify rendering logic - auto-detect content type from `content` field
- [ ] Use heuristics for syntax highlighting (detect language from content)
- [ ] Remove version selector if present
- [ ] Update context menu to work with simplified structure

**Impact:** Major simplification in rendering logic.

#### 2.4 Update Canvas Context
**File:** `frontend/contexts/CanvasContext.tsx`

- [ ] Update state management for simplified artifact structure
- [ ] Remove version tracking logic
- [ ] Simplify artifact update handlers
- [ ] Update artifact persistence logic

**Impact:** Reduces state complexity.

#### 2.5 Update Hooks
**File:** `frontend/hooks/useCanvasMode.ts`

- [ ] Update any artifact-related logic in hooks
- [ ] Simplify artifact state management
- [ ] Remove version handling

**Impact:** Hook simplification.

### Phase 3: Testing & Cleanup

#### 3.1 Update Backend Tests
**Files:** `backend/tests/test_canvas_*.py`

- [ ] Update all test cases to use simplified artifact structure
- [ ] Remove tests for version management
- [ ] Add tests for content streaming with new structure
- [ ] Test artifact cache with new structure
- [ ] Test partial updates with new structure

**Impact:** Test suite needs updates to match new structure.

#### 3.2 Frontend Testing
- [ ] Manual testing of artifact creation
- [ ] Manual testing of artifact updates
- [ ] Test content streaming and display
- [ ] Test different content types (code, markdown, plain text)
- [ ] Verify syntax highlighting still works
- [ ] Test artifact persistence and recreation

**Impact:** Thorough testing needed to ensure no regressions.

#### 3.3 Documentation Updates
**Files:**
- `backend/README.md`
- `backend/ARTIFACT_CACHE_README.md`
- `backend/CANVAS_README.md`
- `frontend/README.md`

- [ ] Update documentation to reflect new simplified structure
- [ ] Remove references to old artifact types
- [ ] Add examples of new artifact structure
- [ ] Update architecture diagrams if present

**Impact:** Documentation reflects new implementation.

## Migration Strategy

### Option 1: Big Bang Replacement
- Implement all changes at once across backend and frontend
- **Pros:** Clean break, no hybrid state
- **Cons:** Higher risk, longer development time

### Option 2: Gradual Migration (Recommended)
1. Create new `Artifact` type alongside existing types
2. Update backend to support both old and new structures
3. Migrate frontend to use new structure
4. Remove old structure after frontend migration complete
5. Clean up deprecated code

**Pros:** Lower risk, can test incrementally  
**Cons:** Temporary code complexity

## Rollback Plan

If issues arise:
1. Revert backend changes first (restore old graph definitions)
2. Revert frontend changes second
3. Use git branches to maintain old implementation
4. Keep artifact cache compatible with both structures during transition

## Success Criteria

- [ ] All artifact operations work with simplified 3-field structure
- [ ] Content streaming works correctly
- [ ] Frontend correctly displays all content types
- [ ] Syntax highlighting works for code content
- [ ] All tests pass
- [ ] No regression in functionality
- [ ] Code is simpler and more maintainable

## Timeline Estimate

- **Phase 1 (Backend):** 1-2 days
- **Phase 2 (Frontend):** 1-2 days
- **Phase 3 (Testing & Cleanup):** 1 day
- **Total:** 3-5 days

## Dependencies

- No external dependencies
- Requires coordination between backend and frontend changes
- Consider using feature flag for gradual rollout

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing artifacts | High | Implement migration script or support both formats temporarily |
| Syntax highlighting issues | Medium | Use robust language detection library |
| Content type detection | Medium | Implement smart heuristics with fallbacks |
| Partial update complexity | Medium | Simplify to full content replacement initially |

## Open Questions

1. Should we keep partial update functionality with simplified structure?
   - **Recommendation:** Yes, but work directly on `content` string with start/end positions
   
2. How do we detect content type (code vs text vs markdown)?
   - **Recommendation:** Use heuristics on frontend (check for code patterns, language indicators)
   
3. Should we add optional `language` or `contentType` hint field?
   - **Recommendation:** Add optional `language` field for explicit hints, but make it optional
   
4. How to handle artifact versioning if needed in future?
   - **Recommendation:** Store versions as separate artifacts with same base ID + version suffix

## Related Documents

- Requirement: [010-revamp-artifact.md](../.docs/0-requirements/010-revamp-artifact.md)
- Backend Architecture: [backend/README.md](../../backend/README.md)
- Canvas Documentation: [backend/CANVAS_README.md](../../backend/CANVAS_README.md)
- Artifact Cache: [backend/ARTIFACT_CACHE_README.md](../../backend/ARTIFACT_CACHE_README.md)

## Notes

- Consider adding optional metadata fields in future (e.g., `created_at`, `updated_at`, `language_hint`)
- Keep the door open for future enhancements without overcomplicating initial implementation
- Frontend auto-detection of content type should be robust enough to handle edge cases
- Ensure backward compatibility during transition period if existing artifacts need to be supported
