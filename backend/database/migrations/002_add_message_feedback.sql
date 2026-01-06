-- Migration 002: Add message_feedbacks table
-- Create table for tracking user feedback (like/dislike) on messages

-- Message feedbacks table
CREATE TABLE IF NOT EXISTS message_feedbacks (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL,
    feedback_type VARCHAR(20) NOT NULL,  -- 'like', 'dislike'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_message_feedbacks_message_id ON message_feedbacks(message_id);
CREATE INDEX IF NOT EXISTS idx_message_feedbacks_type ON message_feedbacks(feedback_type);
