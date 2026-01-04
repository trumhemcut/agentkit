-- Rename agent_type column to agent_id for clarity
-- agent_id is more accurate as it represents an identifier (e.g., "chat", "canvas") not a type

-- For SQLite: SQLite doesn't support ALTER TABLE RENAME COLUMN directly in older versions
-- We need to recreate the table

-- Step 1: Create new table with agent_id
CREATE TABLE IF NOT EXISTS threads_new (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255),
    agent_id VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Copy data from old table (if exists)
INSERT INTO threads_new (id, title, agent_id, model, provider, created_at, updated_at)
SELECT id, title, agent_type, model, provider, created_at, updated_at 
FROM threads
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='threads');

-- Step 3: Drop old table
DROP TABLE IF EXISTS threads;

-- Step 4: Rename new table to threads
ALTER TABLE threads_new RENAME TO threads;

-- Step 5: Recreate index
CREATE INDEX IF NOT EXISTS idx_threads_created_at ON threads(created_at);
