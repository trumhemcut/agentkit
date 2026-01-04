-- Consolidated initial schema for AgentKit database
-- Creates threads and messages tables with all columns and relationships
-- Includes all features from migrations 001-005

-- Threads table
CREATE TABLE IF NOT EXISTS threads (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255),
    agent_id VARCHAR(50) NOT NULL,  -- Identifies the agent type (chat, canvas, salary_viewer, etc.)
    model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    thread_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,  -- Denormalized from threads for easier querying
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',  -- 'text' or 'artifact'
    content TEXT,
    artifact_data TEXT,  -- JSON data for artifacts (charts, canvas, etc.)
    message_metadata TEXT,  -- Additional metadata as JSON
    is_interrupted BOOLEAN NOT NULL DEFAULT 0,  -- Tracks if message was interrupted
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_threads_created_at ON threads(created_at);
CREATE INDEX IF NOT EXISTS idx_threads_agent_id ON threads(agent_id);

CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_agent_id ON messages(agent_id);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);
CREATE INDEX IF NOT EXISTS idx_messages_interrupted ON messages(is_interrupted);
