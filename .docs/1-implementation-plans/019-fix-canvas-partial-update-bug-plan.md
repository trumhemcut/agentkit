# Implementation Plan: Fix Canvas Artifact Partial Update Bug

**Status**: ✅ Implemented (Frontend)  
**Priority**: High  
**Type**: Bug Fix  
**Created**: 2025-12-27
**Implemented**: 2025-12-27

## Problem Summary

When in Canvas mode, users can select text in the artifact panel and click "Chat with agent" to request modifications. However, the current implementation has a critical bug:

**Expected Behavior**:
- Agent generates new text
- New text replaces the exact selected text at the correct position
- Selected text remains highlighted until partial update events are received

**Current Bug**:
- Always replaces at the first position, not at the selected text position
- Other potential issues with selection tracking and content merging

## Root Cause Analysis

### Backend Issues

1. **Selection Position Tracking** ([canvas_agent.py](../../backend/agents/canvas_agent.py))
   - The `_merge_partial_update` method correctly uses `selected_text["start"]` and `selected_text["end"]` 
   - Events are emitted with correct selection boundaries
   - Backend logic appears correct

2. **Event Data Structure** ([canvas_agent.py](../../backend/agents/canvas_agent.py#L604-L656))
   - `ARTIFACT_PARTIAL_UPDATE_START`: Includes correct `selection: {start, end}`
   - `ARTIFACT_PARTIAL_UPDATE_CHUNK`: Includes chunk + selection boundaries
   - `ARTIFACT_PARTIAL_UPDATE_COMPLETE`: Includes final `updatedContent` + selection

### Frontend Issues (PRIMARY SUSPECT)

3. **Frontend Merging Logic** ([CanvasContext.tsx](../../frontend/contexts/CanvasContext.tsx#L79-L100))
   - **BUG LOCATION**: `completePartialUpdate` function
   - Current implementation:
     ```tsx
     const completePartialUpdate = useCallback(() => {
       const { start, end } = partialUpdateSelection
       const newContent = 
         artifact.content.substring(0, start) +
         partialUpdateBuffer +
         artifact.content.substring(end)
       updateArtifactContent(newContent)
     }, [partialUpdateSelection, artifact, partialUpdateBuffer, updateArtifactContent])
     ```
   - **ISSUE**: This logic should work correctly IF `partialUpdateSelection` is set properly
   - Need to verify that `startPartialUpdate(selection)` is called with correct selection

4. **Event Handler** ([ChatContainer.tsx](../../frontend/components/ChatContainer.tsx#L269-L289))
   - Handles `artifact_partial_update_start` event
   - Calls `canvasContext.startPartialUpdate(customEvent.value.selection)`
   - **POTENTIAL BUG**: Need to verify event structure matches expectations

5. **Selection Source** (Need to investigate)
   - Where does the original selection come from when user clicks "Chat with agent"?
   - Is the selection properly passed in the API request?
   - Check: How is `selectedText` sent to backend in the API call?

## Investigation Tasks

### Phase 1: Understand Current Flow (Backend Agent)

1. **Trace Selection Flow Through Backend**
   - [ ] Verify how `selectedText` is received in the API request payload
   - [ ] Check [routes.py](../../backend/api/routes.py) - confirm selection data structure in request
   - [ ] Verify selection is properly passed to `CanvasGraphState`
   - [ ] Confirm backend correctly uses selection in `_build_partial_update_prompt`
   - [ ] Verify events emitted contain correct selection coordinates

   **Expected Findings**:
   - Selection structure: `{start: number, end: number, text: string, lineStart?, lineEnd?}`
   - Backend should emit events with selection boundaries intact

### Phase 2: Trace Selection Flow Through Frontend (Frontend Agent)

2. **Verify Selection Capture**
   - [ ] Find where user text selection is captured in artifact panel
   - [ ] Check how selection is stored (likely in CanvasContext `selectedTextForChat`)
   - [ ] Verify selection data structure matches backend expectations
   - [ ] Confirm character positions are 0-indexed

3. **Verify API Request Construction**
   - [ ] Check API service ([services/api.ts](../../frontend/services/api.ts)) 
   - [ ] Verify `selectedText` is correctly included in POST request body
   - [ ] Confirm selection coordinates are sent as `{start, end, text}`

4. **Verify Event Handling**
   - [ ] Add console logs to event handlers in [ChatContainer.tsx](../../frontend/components/ChatContainer.tsx#L269-L289)
   - [ ] Verify `customEvent.value.selection` contains correct `{start, end}`
   - [ ] Confirm `startPartialUpdate` receives correct selection

5. **Verify Context State Management**
   - [ ] Check if `partialUpdateSelection` state is correctly set
   - [ ] Verify state persists through the streaming process
   - [ ] Confirm `completePartialUpdate` has access to correct selection

## Implementation Plan

### Backend Tasks (Backend Agent)

**Priority**: Low (Backend appears correct, but needs verification)

#### Task 1: Add Diagnostic Logging
- **File**: [backend/agents/canvas_agent.py](../../backend/agents/canvas_agent.py)
- **Action**: Add detailed logging in `_stream_partial_update` method
  ```python
  logger.info(f"[PARTIAL_UPDATE] Received selection: start={selected_text['start']}, end={selected_text['end']}")
  logger.info(f"[PARTIAL_UPDATE] Selected text: {selected_text['text'][:50]}...")
  logger.info(f"[PARTIAL_UPDATE] Full content length: {len(full_content)}")
  ```

#### Task 2: Verify Routes Selection Handling
- **File**: [backend/api/routes.py](../../backend/api/routes.py)
- **Action**: Verify `selectedText` is correctly parsed from request
- **Check**: Ensure selection is passed to state initialization

#### Task 3: Add Integration Test
- **File**: [backend/tests/test_partial_content_editing.py](../../backend/tests/test_partial_content_editing.py)
- **Action**: Add test for selection at different positions (not just start of content)
  ```python
  def test_partial_update_at_middle_position():
      """Test partial update at various positions in content"""
      # Test selection at start, middle, end positions
      # Verify correct replacement happens
  ```

### Frontend Tasks (Frontend Agent)

**Priority**: High (Most likely bug location)

#### Task 1: Add Selection Capture Diagnostics
- **File**: [frontend/components/ArtifactPanel.tsx](../../frontend/components/ArtifactPanel.tsx)
  - OR wherever text selection is captured
- **Action**: 
  - Find the `onSelect` or `onTextSelect` handler
  - Add console logs to verify selection coordinates
  - Verify selection is stored in `selectedTextForChat`

#### Task 2: Verify API Request Construction
- **File**: [frontend/services/api.ts](../../frontend/services/api.ts)
- **Action**:
  - Add logging before sending request
  - Verify `selectedText` is included in request body
  - Confirm structure: `{start: number, end: number, text: string}`

#### Task 3: Add Event Handler Diagnostics
- **File**: [frontend/components/ChatContainer.tsx](../../frontend/components/ChatContainer.tsx#L269-L289)
- **Changes**:
  ```tsx
  case 'artifact_partial_update_start':
    console.log('[DEBUG] Partial update START event:', {
      selection: customEvent.value.selection,
      hasStart: 'start' in customEvent.value.selection,
      hasEnd: 'end' in customEvent.value.selection,
      startValue: customEvent.value.selection?.start,
      endValue: customEvent.value.selection?.end
    });
    if (customEvent.value?.selection) {
      canvasContext.startPartialUpdate(customEvent.value.selection);
    }
    break;
  ```

#### Task 4: Add Context State Diagnostics
- **File**: [frontend/contexts/CanvasContext.tsx](../../frontend/contexts/CanvasContext.tsx)
- **Changes**:
  ```tsx
  const startPartialUpdate = useCallback((selection: { start: number; end: number }) => {
    console.log('[CanvasContext] startPartialUpdate called with:', {
      selection,
      currentArtifactLength: artifact?.content?.length
    });
    setIsPartialUpdateActive(true);
    setPartialUpdateBuffer("");
    setPartialUpdateSelection(selection);
  }, [artifact]);

  const completePartialUpdate = useCallback(() => {
    console.log('[CanvasContext] completePartialUpdate called with:', {
      selection: partialUpdateSelection,
      bufferLength: partialUpdateBuffer.length,
      artifactLength: artifact?.content?.length
    });
    
    if (!partialUpdateSelection || !artifact) {
      console.error('[BUG] Missing selection or artifact:', {
        hasSelection: !!partialUpdateSelection,
        hasArtifact: !!artifact
      });
      return;
    }
    
    const { start, end } = partialUpdateSelection;
    const before = artifact.content.substring(0, start);
    const after = artifact.content.substring(end);
    const newContent = before + partialUpdateBuffer + after;
    
    console.log('[CanvasContext] Merge details:', {
      originalLength: artifact.content.length,
      beforeLength: before.length,
      bufferLength: partialUpdateBuffer.length,
      afterLength: after.length,
      newLength: newContent.length,
      start,
      end
    });
    
    updateArtifactContent(newContent);
    setIsPartialUpdateActive(false);
    setPartialUpdateBuffer("");
    setPartialUpdateSelection(null);
  }, [partialUpdateSelection, artifact, partialUpdateBuffer, updateArtifactContent]);
  ```

#### Task 5: Verify Preview Logic
- **File**: [frontend/components/ArtifactPanel.tsx](../../frontend/components/ArtifactPanel.tsx#L37-L44)
- **Action**: Verify preview during streaming shows correct position
  ```tsx
  if (isPartialUpdateActive && partialUpdateSelection && artifact) {
    const { start, end } = partialUpdateSelection;
    console.log('[ArtifactPanel] Preview update:', {
      start, end, 
      bufferLength: partialUpdateBuffer.length,
      contentLength: artifact.content.length
    });
    return (
      artifact.content.substring(0, start) +
      partialUpdateBuffer +
      artifact.content.substring(end)
    );
  }
  ```

### Testing Strategy

#### Backend Tests (Backend Agent)
1. **Unit Tests**: `test_partial_content_editing.py`
   - Test selection at position 0 (start)
   - Test selection at middle of content
   - Test selection at end of content
   - Test multiple lines selection
   - Test single line selection

2. **Integration Tests**:
   - End-to-end test with mock LLM
   - Verify events contain correct selection data
   - Verify merged content is correct

#### Frontend Tests (Frontend Agent)
1. **Component Tests**:
   - Test selection capture in ArtifactPanel
   - Test event handlers in ChatContainer
   - Test context state updates in CanvasContext

2. **E2E Tests**:
   - Select text at different positions
   - Trigger partial update
   - Verify correct replacement
   - Verify preview during streaming

### Bug Fix Implementation

Based on investigation findings, implement fixes in:

#### If Bug is in Frontend (Most Likely)

**Scenario A: Selection Not Passed to API**
- Fix: Update API call to include selection
- File: `services/api.ts`

**Scenario B: Event Handler Not Reading Selection Correctly**
- Fix: Update event handler to correctly extract selection
- File: `ChatContainer.tsx`

**Scenario C: Context State Not Preserved**
- Fix: Ensure `partialUpdateSelection` state persists
- File: `CanvasContext.tsx`

**Scenario D: Wrong Selection Coordinates**
- Fix: Verify character position calculation
- File: Where selection is captured (ArtifactPanel or Canvas component)

#### If Bug is in Backend (Less Likely)

**Scenario E: Selection Lost in State Management**
- Fix: Ensure selection propagates through state
- File: `canvas_graph.py`, `canvas_agent.py`

## Success Criteria

1. **Functional Requirements**:
   - [ ] Partial update replaces text at exact selected position
   - [ ] Works for selections at start, middle, and end of content
   - [ ] Works for single-line and multi-line selections
   - [ ] Preview during streaming shows correct position
   - [ ] Selection highlighting persists until completion

2. **Testing Requirements**:
   - [ ] All existing tests pass
   - [ ] New tests added for edge cases
   - [ ] Manual testing confirms correct behavior

3. **Documentation Requirements**:
   - [ ] Update knowledge base with findings
   - [ ] Document selection flow diagram
   - [ ] Add troubleshooting guide

## Risk Assessment

**Low Risk**: Changes are primarily diagnostic and bug fixes in existing feature

**Rollback Plan**: 
- All changes are in partial update flow
- Does not affect create/update artifact flows
- Can disable partial update feature if needed

## Timeline Estimate

- **Investigation**: 2-3 hours
- **Implementation**: 2-4 hours
- **Testing**: 2-3 hours
- **Total**: 6-10 hours

## Dependencies

- Backend: LangGraph, FastAPI, existing canvas implementation
- Frontend: React, CanvasContext, AG-UI client
- No external dependencies

## Next Steps

1. **Start Investigation** (Backend Agent + Frontend Agent):
   - Add diagnostic logging to all key points
   - Run manual test with console logs
   - Identify exact failure point

2. **Implement Fix** (Assigned agent based on findings):
   - Fix identified bug
   - Add regression tests
   - Update documentation

3. **Verify Fix**:
   - Run all tests
   - Manual testing in different scenarios
   - Update knowledge base

## Related Files

### Backend
- [backend/agents/canvas_agent.py](../../backend/agents/canvas_agent.py) - Main agent logic
- [backend/graphs/canvas_graph.py](../../backend/graphs/canvas_graph.py) - State definitions
- [backend/api/routes.py](../../backend/api/routes.py) - API endpoints
- [backend/tests/test_partial_content_editing.py](../../backend/tests/test_partial_content_editing.py) - Tests

### Frontend
- [frontend/contexts/CanvasContext.tsx](../../frontend/contexts/CanvasContext.tsx) - Context state
- [frontend/components/ChatContainer.tsx](../../frontend/components/ChatContainer.tsx) - Event handling
- [frontend/components/ArtifactPanel.tsx](../../frontend/components/ArtifactPanel.tsx) - Artifact display
- [frontend/services/api.ts](../../frontend/services/api.ts) - API client

### Documentation
- [.docs/2-knowledge-base/backend/partial-content-editing.md](../../.docs/2-knowledge-base/backend/partial-content-editing.md) - Feature docs

---

## Implementation Summary

### Root Cause Identified

The bug was in the frontend, specifically in [ChatContainer.tsx](../../frontend/components/ChatContainer.tsx#L377-L381). When a user selected text and clicked "Chat with agent", the code hardcoded the selection position to always start at position 0:

```tsx
// BUG: Hardcoded selection always starts at 0
const selectedTextData = selectedTextForChat ? {
  start: 0,  // ❌ WRONG: Always 0
  end: selectedTextForChat.length,  // ❌ WRONG: Only length, not actual position
  text: selectedTextForChat
} : undefined;
```

This meant partial updates always replaced text at the beginning of the artifact, regardless of where the user actually selected.

### Solution Implemented

**1. Updated CanvasContext to store full SelectedText object** ([CanvasContext.tsx](../../frontend/contexts/CanvasContext.tsx))
   - Changed `selectedTextForChat` from `string | null` to `SelectedText | null`
   - This stores the complete selection: `{start: number, end: number, text: string}`

**2. Connected onSelectionChange callback** ([ArtifactPanel.tsx](../../frontend/components/ArtifactPanel.tsx))
   - Added `handleSelectionChange` handler to capture selection with positions
   - Passed `onSelectionChange={handleSelectionChange}` to `TextRenderer`
   - This captures the actual character positions when user selects text

**3. Fixed ChatContainer to use actual selection** ([ChatContainer.tsx](../../frontend/components/ChatContainer.tsx))
   - Changed from hardcoded `{start: 0, end: length}` to using the full `selectedTextForChat` object
   - Now sends correct selection coordinates to backend

**4. Fixed TextRenderer to not overwrite selection** ([TextRenderer.tsx](../../frontend/components/Canvas/TextRenderer.tsx))
   - Removed code that overwrote the full selection object with just text
   - Selection with positions is now preserved from capture to API call

**5. Added comprehensive diagnostic logging**
   - All key points now log selection data for debugging
   - Easy to trace selection flow from capture through merge

### Files Modified

1. **frontend/contexts/CanvasContext.tsx**
   - Updated interface and state to use `SelectedText` type
   - Added detailed logging to `startPartialUpdate` and `completePartialUpdate`

2. **frontend/components/ArtifactPanel.tsx**
   - Added `handleSelectionChange` callback
   - Connected to `TextRenderer` via `onSelectionChange` prop
   - Added logging for selection changes and preview updates

3. **frontend/components/ChatContainer.tsx**
   - Fixed `selectedTextData` to use full object from context
   - Added detailed logging for selection coordinates
   - Enhanced event handler logging

4. **frontend/components/Canvas/TextRenderer.tsx**
   - Removed code that overwrote selection object
   - Selection now flows cleanly from capture to context

### Testing Recommendations

To verify the fix works:

1. **Open Canvas mode** and create or load a text artifact
2. **Select text in the middle** of the artifact (not at the start)
3. **Click "Chat with agent"** and request a modification
4. **Check console logs** to verify:
   - Selection has correct `start` and `end` values (not 0)
   - Backend receives correct selection coordinates
   - Partial update events include correct selection
   - Merge happens at correct position
5. **Verify visually** that text is replaced at the selected position

Test cases to cover:
- Selection at start of artifact
- Selection in middle of artifact
- Selection at end of artifact
- Single-line selection
- Multi-line selection
- Full artifact selection

### Success Criteria

✅ All changes implemented
✅ No TypeScript errors
✅ Diagnostic logging added throughout
✅ Selection flow corrected from capture to merge

**Ready for testing!**
