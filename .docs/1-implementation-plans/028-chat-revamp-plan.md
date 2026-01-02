# 028 - Chat Revamp Implementation Plan

## Requirement Summary
Revamp the chat interface to follow Gemini's design patterns for better user experience and visual comfort. This is a **frontend-only** implementation.

**Reference Images:**
- `.docs/0-requirements/images/gemini-chatting.png` - Chat interaction layout
- `.docs/0-requirements/images/gemini-default.png` - Default empty state

## Key Changes Required

### 1. Chat Container Width Optimization (Desktop)
**Current:** Chat takes 100% of available container space
**Target:** Chat should take ~50% of container width for better reading focus (like Gemini)

### 2. Message Border Removal
**Current:** Agent messages have card borders
**Target:** Remove borders from agent messages for a cleaner, more natural reading experience

### 3. Enhanced Chat Input
**Current:** Simple textarea with send button
**Target:** 
- Larger input area to accommodate additional controls
- Add "+" button (left side) for future file uploads
- Add "Tools" button for features like "Create Image"
- Send button positioned on right side, aligned with "+" and "Tools" buttons

### 4. Default Empty State Position
**Current:** Empty state position not centered optimally
**Target:** Center the chat input vertically when no messages exist (like Gemini default view)

---

## Implementation Tasks

### Frontend Tasks (Delegate to Frontend Agent)

See [frontend.agent.md](.github/agents/frontend.agent.md) for detailed patterns.

**Tech Stack:** NextJS, React, TypeScript, Shadcn UI, Tailwind CSS

#### Task 1: Optimize Chat Container Width (Desktop)

**Files to modify:**
- `frontend/components/ChatContainer.tsx`
- `frontend/components/MessageHistory.tsx`
- `frontend/app/globals.css` (if needed for layout)

**Changes:**
1. Update `ChatContainer` layout to constrain width:
   - Add max-width constraint (~50-60% of viewport or container)
   - Center the chat container horizontally
   - Maintain responsive behavior for mobile
   
2. Update `MessageHistory` to inherit proper width constraints

**CSS Strategy:**
```css
/* Possible approach using max-width and centering */
.chat-container-constrained {
  max-width: 50%; /* or 700px, 800px */
  margin-left: auto;
  margin-right: auto;
}
```

**Considerations:**
- Must work with existing canvas mode (split view)
- Mobile should remain full width
- Ensure proper responsive breakpoints

---

#### Task 2: Remove Agent Message Borders

**Files to modify:**
- `frontend/components/AgentMessageBubble.tsx`

**Changes:**
1. Remove or modify Card component border styles
2. Consider removing Card wrapper entirely or using `border-0` or `shadow-none`
3. Keep padding and spacing for readability
4. Ensure markdown content still renders cleanly

**Current structure:**
```tsx
<Card className="...">
  <CardContent className="...">
    <ReactMarkdown>...</ReactMarkdown>
  </CardContent>
</Card>
```

**Target approach:**
- Remove `Card` border styling
- Use minimal background or no background
- Maintain content padding for readability

**Styling considerations:**
- Preserve markdown rendering quality
- Maintain distinction between user and agent messages
- Test with A2UI surfaces rendering

---

#### Task 3: Enhanced Chat Input with Action Buttons

**Files to modify:**
- `frontend/components/ChatInput.tsx`

**Changes:**
1. Increase input container height and layout flexibility
2. Add "+" button (Plus icon from lucide-react):
   - Position: Left side of input
   - Purpose: Future file upload functionality (stub for now)
   - Styling: Consistent with Send button
   
3. Add "Tools" button (Wrench/Tool icon from lucide-react):
   - Position: Between "+" and Send button
   - Purpose: Future actions like "Create Image"
   - Styling: Consistent with other buttons
   - Can show a dropdown menu placeholder
   
4. Reposition Send button:
   - Position: Right side
   - Align horizontally with "+" and "Tools" buttons
   
5. Maintain keyboard shortcuts (Enter to send, Shift+Enter for new line)

**Layout Structure:**
```tsx
<div className="chat-input-container">
  <div className="action-buttons-row">
    <Button icon={<Plus />} /> {/* File upload placeholder */}
    <Button icon={<Wrench />} /> {/* Tools menu placeholder */}
    <Textarea ... />
    <Button icon={<Send />} /> {/* Send button */}
  </div>
  <p className="hint-text">Press Enter to send...</p>
</div>
```

**Button implementation notes:**
- Use Shadcn UI Button component with `variant="ghost"` or `variant="outline"`
- Icons from `lucide-react`: `Plus`, `Wrench` or `Sparkles`, `Send`
- Tooltips for each button (use Shadcn Tooltip)
- Disabled states when appropriate
- Responsive layout for mobile (may stack or reduce button sizes)

---

#### Task 4: Center Empty State (No Messages)

**Files to modify:**
- `frontend/components/MessageHistory.tsx`
- `frontend/components/ChatContainer.tsx`

**Changes:**
1. When `messages.length === 0`, position chat input in the center of the viewport
2. Use flexbox centering to vertically and horizontally center the empty state
3. Show placeholder text or welcome message
4. Smooth transition when first message appears

**Current empty state structure:**
```tsx
<div className="flex h-full flex-col items-center justify-center text-center">
  <MessageSquare className="mb-4 h-12 w-12 text-muted-foreground" />
  <h3 className="mb-2 text-lg font-semibold">No messages yet</h3>
  <p className="text-sm text-muted-foreground">
    Start a conversation by typing a message below
  </p>
</div>
```

**Target approach:**
- Position chat input container in center when empty
- Keep welcome message but adjust positioning
- Add smooth transition animation when messages appear
- Gemini-style: Large centered input area with welcoming message

**Layout Strategy:**
```tsx
{messages.length === 0 ? (
  <div className="flex h-full items-center justify-center">
    <div className="max-w-2xl w-full px-4">
      <WelcomeMessage />
      <ChatInput /> {/* Centered input */}
    </div>
  </div>
) : (
  <div className="flex flex-col h-full">
    <MessageHistory messages={messages} />
    <ChatInput />
  </div>
)}
```

---

## Testing Requirements

### Visual Testing
1. **Desktop Layout:**
   - Verify chat container is ~50% width and centered
   - Check message borders are removed
   - Validate enhanced input layout (buttons aligned)
   - Test empty state centering
   
2. **Mobile Layout:**
   - Ensure full-width layout is maintained
   - Check button layout responsiveness
   - Verify touch targets are adequate

3. **Canvas Mode:**
   - Verify chat width constraints work with split view
   - Test resizable divider still functions correctly

### Functional Testing
1. Chat input functionality remains unchanged
2. Keyboard shortcuts work (Enter, Shift+Enter)
3. Message sending still functions
4. Smooth transitions between empty and active states
5. Placeholder buttons don't break existing functionality

### Cross-browser Testing
- Chrome, Firefox, Safari, Edge
- Mobile browsers (iOS Safari, Chrome)

---

## Dependencies & Integration Points

### No Backend Changes Required
This is purely a frontend visual update. No API or protocol changes needed.

### Existing Features to Preserve
1. **AG-UI Integration:** Message rendering with A2UI surfaces
2. **Canvas Mode:** Split view functionality
3. **Streaming:** Real-time message updates
4. **Mobile Responsiveness:** Existing mobile layout
5. **Markdown Rendering:** Agent message formatting
6. **Keyboard Shortcuts:** Enter/Shift+Enter behavior

### Style System
- Use Tailwind CSS v4 (as per [tailwind-v4-shadcn-setup.md](.docs/2-knowledge-base/tailwind-v4-shadcn-setup.md))
- Use Shadcn UI components for buttons, inputs
- Follow existing design token patterns

---

## Implementation Order

1. **Task 1** - Chat Container Width (Desktop): Foundation for layout changes
2. **Task 2** - Remove Agent Message Borders: Independent visual change
3. **Task 3** - Enhanced Chat Input: Most complex, builds on layout
4. **Task 4** - Center Empty State: Depends on Task 1 layout changes

---

## Rollout Strategy

### Phase 1: Desktop Improvements
- Implement Tasks 1, 2, 3, 4 for desktop view
- Test thoroughly on desktop browsers

### Phase 2: Mobile Optimization
- Adjust responsive behaviors
- Test on mobile devices
- Ensure touch targets are optimal

### Phase 3: Polish
- Add transitions and animations
- Fine-tune spacing and alignment
- Cross-browser testing
- Performance validation

---

## Success Criteria

✅ Chat container constrained to ~50% width on desktop  
✅ Agent messages render without borders  
✅ Chat input includes "+", "Tools", and "Send" buttons in proper layout  
✅ Empty state shows centered input with welcome message  
✅ Mobile layout remains full-width and responsive  
✅ Canvas mode split view works correctly  
✅ All existing functionality preserved  
✅ Smooth visual transitions  
✅ Accessibility maintained (keyboard navigation, ARIA labels)  

---

## Notes for Frontend Agent

- **Reference Gemini images** in `.docs/0-requirements/images/` for visual guidance
- **Follow Shadcn UI patterns** for button and input components
- **Use Tailwind CSS v4** for styling (check knowledge base for migration guide)
- **Maintain mobile-first responsive design**
- **Test with A2UI components** to ensure no rendering conflicts
- **Preserve all existing keyboard shortcuts and behaviors**
- **Add hover states and tooltips** for new buttons
- **Consider dark mode compatibility**

---

## Knowledge Base Updates

After implementation, update:
- `frontend/README.md` - Document new chat layout patterns
- `.docs/2-knowledge-base/frontend/` - Add chat input enhancement guide
- Screenshots of new layout for future reference
