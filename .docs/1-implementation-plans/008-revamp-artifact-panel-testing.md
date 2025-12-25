# Testing Guide: Artifact Panel Revamp

## Feature Overview
The artifact panel has been revamped with custom text selection and chat integration features:

1. ✅ Default BlockNote context menu is disabled
2. ✅ Custom horizontal context menu appears on text selection
3. ✅ Yellow highlighting of selected text when "Chat with agent" is clicked
4. ✅ Automatic focus on chat input after selection
5. ✅ Right-click context menu is disabled

## Testing Instructions

### Prerequisites
1. Start the frontend dev server: `cd frontend && npm run dev`
2. Start the backend server: `cd backend && python main.py`
3. Navigate to Canvas mode in the application
4. Create a text artifact (markdown/document)

### Test Case 1: Text Selection and Context Menu
**Steps:**
1. Create or open a text artifact in Canvas mode
2. Select any text in the artifact panel
3. Observe the custom horizontal context menu appears above selection

**Expected Result:**
- Custom menu appears with "Chat with agent" button
- Menu is positioned above the selected text
- Menu has a clean horizontal layout with message icon

**Pass Criteria:**
- [ ] Menu appears within 200ms of selection
- [ ] Menu is positioned correctly
- [ ] No default browser context menu appears

---

### Test Case 2: Highlighting Text
**Steps:**
1. Select text in the artifact panel
2. Click "Chat with agent" button in the custom menu
3. Observe the selected text

**Expected Result:**
- Selected text is highlighted in yellow (#FEF08A)
- Highlight persists after menu closes
- Text remains readable with the highlight

**Pass Criteria:**
- [ ] Text is highlighted in yellow
- [ ] Highlight color is clearly visible
- [ ] Highlight doesn't break text formatting

---

### Test Case 3: Chat Input Focus
**Steps:**
1. Select text in the artifact panel
2. Click "Chat with agent" button
3. Observe the chat input field

**Expected Result:**
- Chat input receives focus immediately
- Cursor is in the chat input field
- User can start typing without additional clicks

**Pass Criteria:**
- [ ] Chat input is focused
- [ ] Focus transition is smooth
- [ ] No console errors

---

### Test Case 4: Menu Close Behavior
**Steps:**
1. Select text to open the menu
2. Click outside the menu (but not on "Chat with agent")
3. Observe menu behavior

**Expected Result:**
- Menu closes when clicking outside
- Selected text remains selected
- No highlight is applied

**Alternative Test:**
1. Select text to open menu
2. Press Escape key

**Expected Result:**
- Menu closes on Escape press

**Pass Criteria:**
- [ ] Menu closes on outside click
- [ ] Menu closes on Escape key
- [ ] No errors in console

---

### Test Case 5: Disabled Context Menu
**Steps:**
1. Right-click anywhere in the artifact panel
2. Observe browser behavior

**Expected Result:**
- Default right-click context menu does NOT appear
- No browser context menu is shown

**Pass Criteria:**
- [ ] Right-click is disabled
- [ ] No default context menu appears

---

### Test Case 6: Multiple Highlights
**Steps:**
1. Select text and click "Chat with agent"
2. Select different text and click "Chat with agent" again
3. Observe both highlights

**Expected Result:**
- Both text selections are highlighted
- Highlights don't overlap incorrectly
- All highlights remain visible

**Pass Criteria:**
- [ ] Multiple highlights work
- [ ] Highlights don't conflict
- [ ] All highlights are visible

---

### Test Case 7: Streaming Content
**Steps:**
1. Request agent to update artifact (trigger streaming)
2. Try to select text while content is streaming
3. Observe behavior

**Expected Result:**
- Menu still appears during streaming (if editable is true)
- OR text selection is disabled during streaming

**Pass Criteria:**
- [ ] No errors during streaming
- [ ] Behavior is consistent

---

### Test Case 8: Responsiveness
**Steps:**
1. Resize browser window to different sizes
2. Select text at different positions
3. Observe menu positioning

**Expected Result:**
- Menu adapts to viewport size
- Menu doesn't overflow viewport edges
- Menu remains readable on all screen sizes

**Pass Criteria:**
- [ ] Menu visible on desktop (1920px+)
- [ ] Menu visible on tablet (768px)
- [ ] Menu visible on mobile (375px)

---

## Edge Cases to Test

### Edge Case 1: Long Text Selection
- Select a very long paragraph (multiple lines)
- Menu should appear at the center of selection

### Edge Case 2: Selection at Viewport Edge
- Select text at the top/bottom of the viewport
- Menu should adjust position to remain visible

### Edge Case 3: Empty Selection
- Double-click a word then immediately deselect
- Menu should close if no text is selected

### Edge Case 4: Rapid Selections
- Quickly select multiple different text sections
- Only one menu should be visible at a time

---

## Known Limitations

1. **BlockNote Yjs Warning**: A console warning about Yjs import appears. This is a known BlockNote issue and doesn't affect functionality.

2. **Highlight Persistence**: Highlights are applied using DOM manipulation (span elements). They persist in the rendered view but may not be saved to the markdown content.

3. **Overlapping Highlights**: If two selections overlap, the second highlight may not apply correctly.

---

## Troubleshooting

### Menu Doesn't Appear
- Check console for errors
- Verify selection is not empty
- Check if `showContextMenu` state is updated

### Chat Input Doesn't Focus
- Verify `chatInputRef` is properly registered in CanvasContext
- Check if `ChatInputRef` interface has `focus()` method
- Inspect component hierarchy for ref passing

### Highlighting Doesn't Work
- Check if selection range is valid
- Verify `surroundContents()` isn't failing
- Inspect DOM for `<span class="artifact-highlight">`

### Right-Click Still Shows Browser Menu
- Verify `onContextMenu` handler is on the container
- Check if event.preventDefault() is called

---

## Browser Compatibility

Tested on:
- [ ] Chrome 120+
- [ ] Firefox 120+
- [ ] Safari 17+
- [ ] Edge 120+

---

## Performance Considerations

- Selection detection uses native `selectionchange` event
- Menu positioning calculates on each selection
- Highlights use simple DOM manipulation (lightweight)
- No heavy computations or API calls

---

## Accessibility Notes

- Menu is keyboard accessible (Escape to close)
- Menu uses semantic button elements
- Highlights maintain text contrast ratio
- Focus management follows expected patterns

---

## Next Steps / Future Enhancements

1. **Pre-fill Chat Input**: Automatically insert "Regarding: [selected text]..." in chat input
2. **Highlight Management**: Add UI to view and remove highlights
3. **Multiple Highlight Colors**: Support different highlight colors for categorization
4. **Persistent Highlights**: Save highlights to markdown metadata
5. **AG-UI Integration**: Emit `TEXT_SELECTED` event to backend for analytics
