# Implementation Plan: Markdown Rendering for Chat Messages

**Requirement**: Support markdown formatting when displaying streamed agent responses in chat container.

**Issue**: Currently, agent messages in the chat container display as plain text without markdown rendering support. When the server streams agent responses with markdown formatting (headings, bold, italic, code blocks, lists, etc.), they appear as raw text instead of being properly rendered.

**Goal**: Implement markdown rendering for agent messages only in the chat interface to support rich text formatting while maintaining streaming capabilities. User messages will remain as plain text since users typically chat in raw text.

---

## Overview

This plan adds markdown rendering support to the chat message display system. The implementation focuses on:
1. Installing and configuring a React markdown library
2. Updating MessageBubble component to render markdown content
3. Supporting syntax highlighting for code blocks
4. Ensuring proper styling integration with Shadcn UI
5. Maintaining streaming performance and UX

---

## Frontend Tasks (NextJS + React + TypeScript + Shadcn UI)

**Delegate to Frontend Agent** - See [frontend.agent.md](../.github/agents/frontend.agent.md)

### Task 1: Install Markdown Dependencies

**Dependencies to add:**
```bash
npm install react-markdown remark-gfm rehype-highlight rehype-raw
npm install -D @types/react-syntax-highlighter
```

**Libraries:**
- `react-markdown`: Core markdown rendering for React
- `remark-gfm`: GitHub Flavored Markdown support (tables, strikethrough, task lists)
- `rehype-highlight`: Syntax highlighting for code blocks
- `rehype-raw`: Support for raw HTML in markdown (optional, use carefully)

**File**: `frontend/package.json`

---

### Task 2: Update MessageBubble Component with Markdown Rendering

**File**: `frontend/components/MessageBubble.tsx`

**Changes:**
1. Import markdown dependencies
2. Conditionally render `<ReactMarkdown>` for agent messages only
3. Keep plain text rendering for user messages
4. Configure markdown plugins (GFM, syntax highlighting)
5. Add custom styles for markdown elements
6. Handle streaming content updates

**Implementation approach:**
```tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

// In the CardContent render section:
{(message.isPending || message.isStreaming) && message.content === '' ? (
  <div className="flex items-center gap-2">
    <Loader2 className="h-4 w-4 animate-spin" />
    <span className="text-sm text-muted-foreground">Thinking...</span>
  </div>
) : message.role === 'agent' ? (
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    rehypePlugins={[rehypeHighlight]}
    className="prose prose-sm max-w-none dark:prose-invert"
    components={{
      code: ({ node, inline, className, children, ...props }) => {
        // Custom code rendering with syntax highlighting
      },
      pre: ({ children }) => {
        // Custom pre block styling
      },
      // Additional custom components as needed
    }}
  >
    {message.content}
  </ReactMarkdown>
) : (
  <p className="text-sm whitespace-pre-wrap break-words">
    {message.content}
  </p>
)}
```

**Styling considerations:**
- Use Tailwind's `prose` classes for markdown typography
- Integrate with Shadcn UI's dark/light theme
- Maintain responsive design for code blocks
- Ensure proper text wrapping and overflow handling

---

### Task 3: Add Syntax Highlighting Styles

**File**: `frontend/app/globals.css`

**Changes:**
1. Import highlight.js theme CSS
2. Add custom styles for code blocks
3. Ensure dark/light theme compatibility

**Implementation:**
```css
/* Add to globals.css */
@import 'highlight.js/styles/github-dark.css';

/* Custom code block styling */
.markdown-content pre {
  @apply rounded-lg p-4 overflow-x-auto;
}

.markdown-content code {
  @apply text-sm font-mono;
}

/* Inline code styling */
.markdown-content :not(pre) > code {
  @apply bg-muted px-1.5 py-0.5 rounded text-sm;
}
```

---

### Task 4: Handle Streaming Content with Markdown

**File**: `frontend/components/MessageBubble.tsx`

**Considerations:**
- Markdown rendering should work seamlessly with streaming content
- React-markdown re-renders as content chunks arrive
- Handle incomplete markdown syntax during streaming (e.g., partial code blocks)
- Show loading spinner only when content is empty

**Approach:**
- Keep existing streaming logic in ChatContainer
- Let MessageBubble re-render with updated markdown content
- React-markdown handles incremental content gracefully
- Add buffer handling for incomplete markdown tokens if needed

---

### Task 5: Test Markdown Rendering

**File**: Manual testing + potential test file

**Test cases:**
1. **Basic formatting**: Bold, italic, strikethrough
2. **Headings**: H1-H6 levels
3. **Lists**: Ordered and unordered lists
4. **Code blocks**: Inline code and fenced code blocks with syntax highlighting
5. **Links**: Hyperlinks with proper rendering
6. **Tables**: GitHub-flavored markdown tables
7. **Blockquotes**: Quote formatting
8. **Streaming**: Markdown rendering during progressive message streaming
9. **Dark/Light themes**: Proper styling in both modes
10. **Long content**: Proper scrolling and overflow handling

---

## Backend Tasks (Optional - Content Generation)

**Delegate to Backend Agent** - See [backend.agent.md](../.github/agents/backend.agent.md)

### Task 6: Ensure Backend Generates Valid Markdown (Optional)

**Files**: 
- `backend/agents/chat_agent.py`
- `backend/agents/canvas_agent.py`

**Changes** (if needed):
- Verify that LLM responses include proper markdown formatting
- Ensure streaming chunks don't break markdown syntax mid-token
- Add system prompts encouraging markdown usage for code, lists, formatting

**Note**: Most LLMs already generate markdown naturally. This task is only needed if output formatting needs improvement.

---

## Integration Points

### AG-UI Protocol (No changes needed)
- `TEXT_MESSAGE_CHUNK` events already carry text content
- Frontend assembles chunks into `message.content`
- Markdown rendering happens at display layer
- No protocol changes required

### Component Integration Flow:
1. Backend streams `TEXT_MESSAGE_CHUNK` events
2. `ChatContainer` assembles chunks via `useAGUI` hook
3. `MessageBubble` receives `message.content` with markdown
4. `ReactMarkdown` renders formatted content
5. Shadcn UI styles integrate with prose classes

---

## Technical Considerations

### Performance
- React-markdown is lightweight and optimized for React
- Syntax highlighting adds minimal overhead
- Streaming performance unaffected (rendering happens in component)

### Security
- React-markdown escapes HTML by default (safe from XSS)
- Only enable `rehype-raw` if trusted HTML input is required
- User messages kept as plain text (no markdown parsing needed)
- Only agent responses are parsed for markdown (trusted source)

### Accessibility
- Markdown semantic HTML improves screen reader support
- Code blocks have proper language labels
- Links have proper ARIA attributes

### Styling
- Integrate with existing Shadcn UI theme
- Maintain responsive design
- Support dark/light mode switching
- Proper color contrast for code syntax

---

## Dependencies

- **Frontend**: Task 1 must complete before Task 2
- **Testing**: Task 5 depends on Tasks 2-4 completion
- **Backend**: Task 6 is independent and optional

---

## Testing Strategy

### Unit Tests (Frontend)
- Test MessageBubble renders markdown correctly
- Test code block syntax highlighting
- Test dark/light theme styling

### Integration Tests
- Test streaming message with markdown
- Test markdown rendering in ChatContainer
- Test Canvas chat markdown rendering

### Manual Testing
- Verify all markdown elements render correctly
- Test real-time streaming with markdown
- Test copy-paste from rendered markdown
- Test mobile responsiveness

---

## Implementation Order

1. ✅ **Frontend Task 1**: Install markdown dependencies
2. ✅ **Frontend Task 2**: Update MessageBubble with markdown rendering
3. ✅ **Frontend Task 3**: Add syntax highlighting styles
4. ✅ **Frontend Task 4**: Test streaming integration
5. ✅ **Frontend Task 5**: Comprehensive testing
6. 🔧 **Backend Task 6**: (Optional) Verify markdown output quality

---

## Expected Outcomes

### User Experience
- Agent messages display with rich formatting (bold, italic, headings)
- Code blocks in agent responses have syntax highlighting
- Lists and tables render properly in agent responses
- Links in agent messages are clickable
- User messages remain as plain text (natural for raw text input)
- Markdown works seamlessly with streaming agent responses

### Developer Experience
- Easy to maintain markdown configuration
- Consistent styling with Shadcn UI
- Good TypeScript type safety
- Clear component boundaries

### Performance
- No noticeable impact on streaming speed
- Smooth rendering during message updates
- Efficient syntax highlighting

---

## Knowledge Base Updates

After implementation, update:
- `/.docs/2-knowledge-base/frontend-components.md` - Document MessageBubble markdown rendering
- `/.docs/2-knowledge-base/styling-guide.md` - Document markdown styling patterns
- `/.docs/2-knowledge-base/chat-system.md` - Document markdown support in chat flow

---

## References

- [react-markdown documentation](https://github.com/remarkjs/react-markdown)
- [remark-gfm (GitHub Flavored Markdown)](https://github.com/remarkjs/remark-gfm)
- [rehype-highlight (Syntax highlighting)](https://github.com/rehypejs/rehype-highlight)
- [Tailwind Typography (prose classes)](https://tailwindcss.com/docs/typography-plugin)
- [Shadcn UI theming](https://ui.shadcn.com/docs/theming)
