# Components Guide

## Layout Components

### Header

**Location**: `components/Header.tsx`

**Purpose**: Application header with branding and title.

**Usage**:
```tsx
import { Header } from '@/components/Header';

<Header />
```

**Features**:
- App logo with Bot icon
- Application title and tagline
- Fixed height (h-16)

---

### Sidebar

**Location**: `components/Sidebar.tsx`

**Purpose**: Thread list sidebar with chat management.

**Props**:
```typescript
interface SidebarProps {
  threads: Thread[];
  currentThreadId: string | null;
  onNewChat: () => void;
  onSelectThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
}
```

**Features**:
- New Chat button
- Scrollable thread list
- Thread selection highlighting
- Delete thread button (visible on hover)
- Empty state display
- Date formatting (Today, Yesterday, X days ago)

**Usage**:
```tsx
<Sidebar
  threads={threads}
  currentThreadId={currentThreadId}
  onNewChat={createThread}
  onSelectThread={selectThread}
  onDeleteThread={deleteThread}
/>
```

---

### Layout

**Location**: `components/Layout.tsx`

**Purpose**: Main layout composition with header, sidebar, and content area.

**Props**:
```typescript
interface LayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
}
```

**Usage**:
```tsx
<Layout sidebar={<Sidebar {...props} />}>
  <ChatContainer />
</Layout>
```

---

## Chat Components

### ChatContainer

**Location**: `components/ChatContainer.tsx`

**Purpose**: Main chat interface with message history and input.

**Props**:
```typescript
interface ChatContainerProps {
  threadId: string | null;
  onUpdateThreadTitle: (threadId: string, title: string) => void;
}
```

**Features**:
- Integrates ChatHistory and ChatInput
- Manages AG-UI event handling
- Handles message streaming
- Auto-updates thread title from first message
- Loading states and error handling

**AG-UI Event Handling**:
- `RUN_STARTED`: Agent begins processing
- `TEXT_MESSAGE_CHUNK`: Streaming message content
- `RUN_FINISHED`: Agent completes response
- `ERROR`: Error occurred

---

### ChatHistory

**Location**: `components/ChatHistory.tsx`

**Purpose**: Displays list of messages with scrolling.

**Props**:
```typescript
interface ChatHistoryProps {
  messages: Message[];
  scrollRef?: React.RefObject<HTMLDivElement>;
}
```

**Features**:
- Scrollable message list
- Empty state display
- Auto-scroll support via ref

---

### MessageBubble

**Location**: `components/MessageBubble.tsx`

**Purpose**: Individual message display with avatar and content.

**Props**:
```typescript
interface MessageBubbleProps {
  message: Message;
}
```

**Features**:
- User/Agent avatar icons
- Message content in Card
- Timestamp formatting
- Agent name display
- Role-based styling (user: right-aligned, agent: left-aligned)

---

### ChatInput

**Location**: `components/ChatInput.tsx`

**Purpose**: Message input box with send button.

**Props**:
```typescript
interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

**Features**:
- Multi-line textarea
- Send button
- Enter to send (Shift+Enter for new line)
- Disabled state during agent response
- Character counter (optional)

---

### AvatarIcon

**Location**: `components/AvatarIcon.tsx`

**Purpose**: User or agent avatar with icon.

**Props**:
```typescript
interface AvatarIconProps {
  role: 'user' | 'agent';
  className?: string;
}
```

**Features**:
- User icon (blue background)
- Agent icon (green background)
- Lucide icons (User, Bot)
- Customizable styling

---

## UI Components (Shadcn UI)

### Button

Located in `components/ui/button.tsx`

**Variants**: default, destructive, outline, secondary, ghost, link
**Sizes**: default, sm, lg, icon

### Input

Located in `components/ui/input.tsx`

Standard text input with consistent styling.

### Textarea

Located in `components/ui/textarea.tsx`

Multi-line text input with auto-resize.

### Card

Located in `components/ui/card.tsx`

Container with border and shadow. Sub-components:
- CardHeader
- CardTitle
- CardDescription
- CardContent
- CardFooter

### ScrollArea

Located in `components/ui/scroll-area.tsx`

Scrollable area with custom scrollbar styling.

### Avatar

Located in `components/ui/avatar.tsx`

Avatar component with image and fallback support.

### Separator

Located in `components/ui/separator.tsx`

Horizontal or vertical separator line.

---

## Styling Conventions

- Use Tailwind CSS utility classes
- Follow Shadcn UI design tokens (primary, secondary, muted, etc.)
- Responsive design with mobile-first approach
- Dark mode support via CSS variables
- Use `cn()` utility for conditional classes

---

## Best Practices

1. **Component Composition**: Break down complex components into smaller, reusable pieces
2. **Type Safety**: Always define TypeScript interfaces for props
3. **Accessibility**: Use semantic HTML and ARIA labels
4. **Performance**: Use React.memo for expensive components
5. **Error Handling**: Always handle loading and error states
