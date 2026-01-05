# Implementation Plan: Message Feedback Actions (Like, Dislike, Copy, Retry)

**Requirement**: [032-like-dislike-copy-and-retry.md](../.docs/0-requirements/032-like-dislike-copy-and-retry.md)

## Overview

Add interactive feedback actions to agent message responses, similar to ChatGPT:
- **Copy**: Copy message content to clipboard
- **Like** (👍): Positive feedback for the response
- **Dislike** (👎): Negative feedback for the response  
- **Retry** (🔄): Regenerate the response

These actions will appear as icon buttons below each agent message, providing users with ways to interact with and provide feedback on agent responses.

---

## Architecture

### 1. Backend (LangGraph + FastAPI)
**Delegate to Backend Agent** - See [backend.agent.md](../.github/agents/backend.agent.md)

#### 1.1 Database Schema Extension
**File**: `backend/database/models.py`

Add a new `MessageFeedback` model to track user feedback:

```python
class MessageFeedback(Base):
    """
    Message feedback model for tracking user reactions (like/dislike).
    
    Attributes:
        id: Unique feedback identifier (UUID)
        message_id: Foreign key to the message
        feedback_type: Type of feedback ("like" or "dislike")
        created_at: Timestamp when feedback was given
        message: Relationship to the message
    """
    __tablename__ = "message_feedbacks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False)
    feedback_type = Column(String(20), nullable=False)  # "like", "dislike"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    message = relationship("Message", back_populates="feedbacks")
```

Update `Message` model:
```python
class Message(Base):
    # ... existing fields ...
    
    # Relationships
    thread = relationship("Thread", back_populates="messages")
    feedbacks = relationship("MessageFeedback", back_populates="message", cascade="all, delete-orphan")
```

#### 1.2 Database Migration
**File**: `backend/database/migrations/002_add_message_feedback.py`

Create migration script:
```python
"""Add message_feedbacks table

Revision ID: 002
Revises: 001
Create Date: 2026-01-05
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'message_feedbacks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('message_id', sa.String(36), sa.ForeignKey('messages.id'), nullable=False),
        sa.Column('feedback_type', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_message_feedbacks_message_id', 'message_feedbacks', ['message_id'])


def downgrade():
    op.drop_index('ix_message_feedbacks_message_id', 'message_feedbacks')
    op.drop_table('message_feedbacks')
```

#### 1.3 API Models
**File**: `backend/api/models.py`

Add request/response models:

```python
from pydantic import BaseModel
from typing import Literal

class MessageFeedbackRequest(BaseModel):
    """Request model for submitting message feedback."""
    feedback_type: Literal["like", "dislike"]
    
class MessageFeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    success: bool
    message_id: str
    feedback_type: str
```

#### 1.4 Feedback Service
**File**: `backend/services/feedback_service.py` (new)

Create service for feedback operations:

```python
"""Service for handling message feedback operations."""

from sqlalchemy.orm import Session
from database.models import MessageFeedback, Message
from typing import Optional
import uuid


class FeedbackService:
    """Service for managing message feedback."""
    
    @staticmethod
    async def add_feedback(
        db: Session,
        message_id: str,
        feedback_type: str
    ) -> MessageFeedback:
        """
        Add or update feedback for a message.
        
        If feedback already exists for this message, it will be updated.
        Otherwise, a new feedback entry is created.
        """
        # Check if message exists
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        # Check if feedback already exists
        existing = db.query(MessageFeedback).filter(
            MessageFeedback.message_id == message_id
        ).first()
        
        if existing:
            # Update existing feedback
            existing.feedback_type = feedback_type
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new feedback
            feedback = MessageFeedback(
                id=str(uuid.uuid4()),
                message_id=message_id,
                feedback_type=feedback_type
            )
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            return feedback
    
    @staticmethod
    async def remove_feedback(
        db: Session,
        message_id: str
    ) -> bool:
        """Remove feedback for a message."""
        feedback = db.query(MessageFeedback).filter(
            MessageFeedback.message_id == message_id
        ).first()
        
        if feedback:
            db.delete(feedback)
            db.commit()
            return True
        return False
    
    @staticmethod
    async def get_feedback(
        db: Session,
        message_id: str
    ) -> Optional[MessageFeedback]:
        """Get feedback for a message."""
        return db.query(MessageFeedback).filter(
            MessageFeedback.message_id == message_id
        ).first()
```

#### 1.5 API Endpoints
**File**: `backend/api/routers/messages.py`

Add feedback endpoints:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.models import MessageFeedbackRequest, MessageFeedbackResponse
from api.dependencies import get_db
from services.feedback_service import FeedbackService

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/{message_id}/feedback", response_model=MessageFeedbackResponse)
async def submit_feedback(
    message_id: str,
    request: MessageFeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit or update feedback for a message."""
    try:
        feedback = await FeedbackService.add_feedback(
            db=db,
            message_id=message_id,
            feedback_type=request.feedback_type
        )
        return MessageFeedbackResponse(
            success=True,
            message_id=message_id,
            feedback_type=feedback.feedback_type
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.delete("/{message_id}/feedback")
async def remove_feedback(
    message_id: str,
    db: Session = Depends(get_db)
):
    """Remove feedback for a message."""
    success = await FeedbackService.remove_feedback(db=db, message_id=message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"success": True}

@router.get("/{message_id}/feedback")
async def get_feedback(
    message_id: str,
    db: Session = Depends(get_db)
):
    """Get feedback for a message."""
    feedback = await FeedbackService.get_feedback(db=db, message_id=message_id)
    if not feedback:
        return {"feedback_type": None}
    return {"feedback_type": feedback.feedback_type}
```

Register router in `backend/main.py`:
```python
from api.routers import messages

app.include_router(messages.router, prefix="/api")
```

#### 1.6 Retry Functionality
**File**: `backend/api/routers/agents.py`

Add retry endpoint that re-runs the last user message:

```python
@router.post("/{agent_id}/retry/{thread_id}/{message_id}")
async def retry_message(
    agent_id: str,
    thread_id: str,
    message_id: str,
    db: Session = Depends(get_db)
):
    """
    Retry generating a response for a specific assistant message.
    
    This will:
    1. Find the user message that preceded the given assistant message
    2. Delete the assistant message
    3. Re-run the agent with the same user message
    
    Returns SSE stream with new response.
    """
    # Get the message to retry
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message or message.role != "assistant":
        raise HTTPException(status_code=404, detail="Assistant message not found")
    
    # Find the preceding user message
    user_message = db.query(Message).filter(
        Message.thread_id == thread_id,
        Message.role == "user",
        Message.created_at < message.created_at
    ).order_by(Message.created_at.desc()).first()
    
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found to retry")
    
    # Delete the assistant message
    db.delete(message)
    db.commit()
    
    # Re-run the agent with the user message
    # This follows the same pattern as the regular message endpoint
    # ... (implementation similar to existing send_message endpoint)
```

---

### 2. Protocol (Message Feedback)

#### Message Feedback State
Frontend tracks feedback state locally and syncs with backend:

**Local State (Frontend)**:
```typescript
interface MessageFeedback {
  messageId: string;
  feedbackType: 'like' | 'dislike' | null;
}
```

**API Communication**:
- **POST** `/api/messages/{message_id}/feedback` - Submit like/dislike
- **DELETE** `/api/messages/{message_id}/feedback` - Remove feedback
- **GET** `/api/messages/{message_id}/feedback` - Get current feedback

#### Copy Action
Copy action is client-side only (no backend):
- Uses browser Clipboard API
- Copies markdown content of the message
- Shows toast notification on success

#### Retry Action
Retry triggers backend re-generation:
- **POST** `/api/agents/{agent_id}/retry/{thread_id}/{message_id}`
- Returns SSE stream with new response
- Frontend deletes old message and displays new stream

---

### 3. Frontend (NextJS + Shadcn UI + AG-UI)
**Delegate to Frontend Agent** - See [frontend.agent.md](../.github/agents/frontend.agent.md)

#### 3.1 Message Actions Component
**File**: `frontend/components/MessageActions.tsx` (new)

Create reusable action buttons component:

```tsx
'use client';

import { Button } from '@/components/ui/button';
import { 
  ThumbsUp, 
  ThumbsDown, 
  Copy, 
  RotateCw 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';

interface MessageActionsProps {
  messageId: string;
  messageContent: string;
  onRetry?: () => void;
  className?: string;
  initialFeedback?: 'like' | 'dislike' | null;
}

export function MessageActions({ 
  messageId, 
  messageContent, 
  onRetry,
  className,
  initialFeedback = null
}: MessageActionsProps) {
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(initialFeedback);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(messageContent);
      toast({
        title: "Copied to clipboard",
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: "Failed to copy",
        variant: "destructive",
        duration: 2000,
      });
    }
  };

  const handleFeedback = async (type: 'like' | 'dislike') => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      // If clicking the same feedback, remove it
      if (feedback === type) {
        await fetch(`/api/messages/${messageId}/feedback`, {
          method: 'DELETE',
        });
        setFeedback(null);
      } else {
        // Submit new feedback
        await fetch(`/api/messages/${messageId}/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ feedback_type: type }),
        });
        setFeedback(type);
      }
    } catch (error) {
      toast({
        title: "Failed to submit feedback",
        variant: "destructive",
        duration: 2000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {/* Copy Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleCopy}
        className="h-8 w-8 p-0 hover:bg-muted"
        title="Copy message"
      >
        <Copy className="h-4 w-4" />
      </Button>

      {/* Like Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleFeedback('like')}
        disabled={isSubmitting}
        className={cn(
          "h-8 w-8 p-0 hover:bg-muted",
          feedback === 'like' && "bg-muted text-green-600"
        )}
        title="Good response"
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>

      {/* Dislike Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleFeedback('dislike')}
        disabled={isSubmitting}
        className={cn(
          "h-8 w-8 p-0 hover:bg-muted",
          feedback === 'dislike' && "bg-muted text-red-600"
        )}
        title="Bad response"
      >
        <ThumbsDown className="h-4 w-4" />
      </Button>

      {/* Retry Button */}
      {onRetry && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onRetry}
          className="h-8 w-8 p-0 hover:bg-muted"
          title="Regenerate response"
        >
          <RotateCw className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
```

#### 3.2 Update AgentMessageBubble
**File**: `frontend/components/AgentMessageBubble.tsx`

Integrate MessageActions component:

```tsx
import { MessageActions } from './MessageActions';

export function AgentMessageBubble({ 
  message, 
  onEnableCanvas, 
  canvasModeActive, 
  threadId,
  agentId,
  onActionEvent,
  onRetry // Add new prop
}: AgentMessageBubbleProps) {
  // ... existing code ...
  
  const handleRetry = () => {
    if (onRetry) {
      onRetry(message.id);
    }
  };

  return (
    <div className={/* ... */}>
      <div className="flex flex-col gap-1 w-full">
        {/* ... existing message content ... */}
        
        {/* Actions row */}
        <div className="flex items-center gap-2 px-3">
          <span className="text-xs text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>
          
          {/* Show actions only for completed messages */}
          {!message.isPending && !message.isStreaming && (
            <MessageActions
              messageId={message.id}
              messageContent={message.content}
              onRetry={threadId ? handleRetry : undefined}
              className="ml-auto"
            />
          )}
          
          {/* Canvas button (existing) */}
          {isArtifactMessage(message) && !message.isStreaming && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEnableCanvas}
              className="h-6 px-2 text-xs flex items-center gap-1"
            >
              <Edit className="h-3 w-3" />
              Edit in Canvas
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
```

Update interface:
```tsx
interface AgentMessageBubbleProps {
  message: Message;
  onEnableCanvas?: (message: Message) => void;
  canvasModeActive?: boolean;
  threadId?: string | null;
  agentId?: string;
  onActionEvent?: (event: any) => void;
  onRetry?: (messageId: string) => void; // New prop
}
```

#### 3.3 Update ChatContainer
**File**: `frontend/components/ChatContainer.tsx`

Add retry handler:

```tsx
const handleRetry = async (messageId: string) => {
  if (!currentThreadId || !currentAgentId) return;
  
  setIsLoading(true);
  
  try {
    // Call retry endpoint which returns SSE stream
    const response = await fetch(
      `/api/agents/${currentAgentId}/retry/${currentThreadId}/${messageId}`,
      { method: 'POST' }
    );
    
    if (!response.ok) throw new Error('Retry failed');
    
    // Remove the old message from UI
    setMessages(prev => prev.filter(m => m.id !== messageId));
    
    // Process the new SSE stream
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response stream');
    
    // Create new assistant message
    const newMessage: Message = {
      id: generateUniqueId('msg'),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isPending: false,
      isStreaming: true,
      agentId: currentAgentId,
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // Process stream events (similar to existing sendMessage logic)
    // ... stream processing code ...
    
  } catch (error) {
    console.error('Retry failed:', error);
    toast({
      title: "Failed to retry",
      description: "Please try again",
      variant: "destructive",
    });
  } finally {
    setIsLoading(false);
  }
};

// Pass to MessageHistory
<MessageHistory
  messages={messages}
  scrollRef={scrollRef}
  onEnableCanvas={handleEnableCanvas}
  onScroll={handleScroll}
  canvasModeActive={canvasMode}
  threadId={currentThreadId}
  onActionEvent={handleAgentAction}
  onRetry={handleRetry} // New prop
/>
```

#### 3.4 Update MessageHistory and MessageBubble
**File**: `frontend/components/MessageHistory.tsx`

```tsx
interface MessageHistoryProps {
  // ... existing props ...
  onRetry?: (messageId: string) => void; // New prop
}

export function MessageHistory({ 
  messages, 
  scrollRef, 
  onEnableCanvas, 
  onScroll, 
  canvasModeActive, 
  threadId, 
  onActionEvent,
  onRetry // New prop
}: MessageHistoryProps) {
  return (
    <div className="h-full overflow-y-auto w-full" ref={scrollRef} onScroll={onScroll}>
      <div className={/* ... */}>
        {messages.map((message) => (
          <MessageBubble 
            key={message.id} 
            message={message} 
            onEnableCanvas={onEnableCanvas} 
            canvasModeActive={canvasModeActive}
            threadId={threadId}
            onActionEvent={onActionEvent}
            onRetry={onRetry} // Pass through
          />
        ))}
      </div>
    </div>
  );
}
```

**File**: `frontend/components/MessageBubble.tsx`

```tsx
interface MessageBubbleProps {
  // ... existing props ...
  onRetry?: (messageId: string) => void; // New prop
}

export function MessageBubble({ 
  message, 
  onEnableCanvas, 
  canvasModeActive, 
  threadId, 
  onActionEvent,
  onRetry // New prop
}: MessageBubbleProps) {
  if (message.role === 'user') {
    return <UserMessageBubble message={message} canvasModeActive={canvasModeActive} />;
  }
  
  return (
    <AgentMessageBubble 
      message={message} 
      onEnableCanvas={onEnableCanvas} 
      canvasModeActive={canvasModeActive} 
      threadId={threadId}
      onActionEvent={onActionEvent}
      onRetry={onRetry} // Pass through
    />
  );
}
```

#### 3.5 API Service
**File**: `frontend/services/api.ts`

Add feedback API functions:

```typescript
export async function submitMessageFeedback(
  messageId: string,
  feedbackType: 'like' | 'dislike'
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/messages/${messageId}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ feedback_type: feedbackType }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to submit feedback');
  }
}

export async function removeMessageFeedback(messageId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/messages/${messageId}/feedback`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error('Failed to remove feedback');
  }
}

export async function getMessageFeedback(
  messageId: string
): Promise<{ feedback_type: 'like' | 'dislike' | null }> {
  const response = await fetch(`${API_BASE_URL}/messages/${messageId}/feedback`);
  
  if (!response.ok) {
    throw new Error('Failed to get feedback');
  }
  
  return response.json();
}
```

#### 3.6 Load Feedback State on Mount
**File**: `frontend/components/MessageActions.tsx`

Load initial feedback state from backend:

```tsx
useEffect(() => {
  const loadFeedback = async () => {
    try {
      const data = await getMessageFeedback(messageId);
      setFeedback(data.feedback_type);
    } catch (error) {
      console.error('Failed to load feedback:', error);
    }
  };
  
  loadFeedback();
}, [messageId]);
```

---

## Testing Strategy

### Backend Tests
**File**: `backend/tests/test_message_feedback.py`

```python
def test_submit_like_feedback():
    """Test submitting like feedback."""
    # ... test implementation

def test_submit_dislike_feedback():
    """Test submitting dislike feedback."""
    # ... test implementation

def test_update_existing_feedback():
    """Test updating existing feedback."""
    # ... test implementation

def test_remove_feedback():
    """Test removing feedback."""
    # ... test implementation

def test_retry_message():
    """Test retry endpoint."""
    # ... test implementation
```

### Frontend Tests
**File**: `frontend/tests/components/MessageActions.test.tsx`

```tsx
describe('MessageActions', () => {
  it('copies message to clipboard', async () => {
    // ... test implementation
  });

  it('submits like feedback', async () => {
    // ... test implementation
  });

  it('toggles feedback on second click', async () => {
    // ... test implementation
  });

  it('triggers retry callback', () => {
    // ... test implementation
  });
});
```

---

## Implementation Sequence

### Phase 1: Backend Foundation
1. ✅ Create `MessageFeedback` model
2. ✅ Create database migration
3. ✅ Implement `FeedbackService`
4. ✅ Add feedback API endpoints
5. ✅ Add retry endpoint
6. ✅ Write backend tests

### Phase 2: Frontend Components
1. ✅ Create `MessageActions` component
2. ✅ Integrate with `AgentMessageBubble`
3. ✅ Add retry handler to `ChatContainer`
4. ✅ Update prop chains through `MessageHistory` and `MessageBubble`
5. ✅ Add API service functions
6. ✅ Write frontend tests

### Phase 3: Integration & Polish
1. ✅ Test end-to-end feedback flow
2. ✅ Test retry functionality
3. ✅ Verify mobile responsiveness
4. ✅ Add loading states and error handling
5. ✅ Update documentation

---

## UI/UX Considerations

### Button Layout
- Place action buttons below message content, aligned to the right
- Show only for completed messages (not streaming/pending)
- Use subtle hover effects similar to ChatGPT
- On mobile: ensure buttons are touch-friendly (minimum 44px tap target)

### Visual States
- **Default**: Gray ghost buttons
- **Hover**: Light background highlight
- **Active Feedback**: 
  - Like: Green tint
  - Dislike: Red tint
- **Disabled**: Reduced opacity during submission

### Spacing
- 4px gap between action buttons
- 8px margin from timestamp
- Align with message content padding

### Accessibility
- Add `title` attributes for tooltips
- Ensure keyboard navigation works
- Add ARIA labels for screen readers
- Maintain sufficient contrast ratios

---

## Dependencies

- **Lucide React**: Icons already installed (ThumbsUp, ThumbsDown, Copy, RotateCw)
- **Shadcn UI**: Button, Toast components
- **Browser API**: Clipboard API for copy functionality
- **Database**: SQLAlchemy migration required

---

## Edge Cases

1. **Offline Mode**: Copy works offline, feedback/retry require connection
2. **Streaming Messages**: Hide actions until streaming completes
3. **Interrupted Messages**: Show actions, retry generates new response
4. **Artifact Messages**: Show actions alongside "Edit in Canvas" button
5. **Multiple Retries**: Each retry deletes previous attempt
6. **Feedback History**: Only stores latest feedback per message (not historical)

---

## Success Criteria

- ✅ Copy button successfully copies message content to clipboard
- ✅ Like/dislike buttons persist feedback to database
- ✅ Feedback state is visually indicated with color
- ✅ Retry button regenerates response and replaces old message
- ✅ Actions are hidden during streaming
- ✅ Mobile layout maintains usability
- ✅ All tests pass
- ✅ Follows ChatGPT-like UX patterns

---

## Future Enhancements

- Feedback analytics dashboard for agent performance
- Feedback comments/reasons for dislike
- Share message functionality
- Export conversation with feedback data
- A/B testing different response variations
- Feedback-based model fine-tuning
