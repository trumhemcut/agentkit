/**
 * Database persistence types
 * 
 * Types for interacting with the backend database persistence layer.
 * Based on the API contracts defined in the implementation plan.
 */

/**
 * Thread represents a conversation thread stored in the database
 */
export interface Thread {
  id: string;
  title: string;
  agent_id: string;    // "chat" | "canvas" | "salary_viewer"
  model: string;       // "gpt-5-mini" | "gemini-2.5-flash" | etc.
  provider: string;    // "azure-openai" | "gemini" | "ollama"
  created_at: string;  // ISO 8601 timestamp
  updated_at: string;  // ISO 8601 timestamp
}

/**
 * Message represents a single message in a conversation thread
 */
export interface Message {
  id: string;
  thread_id: string;
  agent_id: string;    // "chat" | "canvas" | "salary_viewer" - denormalized for easier querying
  role: "user" | "assistant";
  message_type: "text" | "artifact";  // Message type for easy identification
  content: string | null;
  artifact_data: Record<string, any> | null;
  metadata: Record<string, any> | null;
  is_interrupted: boolean;  // True if user clicked Stop button
  created_at: string;  // ISO 8601 timestamp
}

/**
 * Request payload for creating a new thread
 */
export interface CreateThreadRequest {
  agent_id: string;
  model: string;
  provider: string;
  title?: string;
}

/**
 * Request payload for updating a thread
 */
export interface UpdateThreadRequest {
  title?: string;
}

/**
 * Request payload for creating a new message
 */
export interface CreateMessageRequest {
  role: "user" | "assistant";
  content?: string;
  artifact_data?: Record<string, any>;
  metadata?: Record<string, any>;
}

/**
 * Response when listing threads
 */
export interface ListThreadsResponse {
  threads: Thread[];
}

/**
 * Response when listing messages
 */
export interface ListMessagesResponse {
  messages: Message[];
}

/**
 * Response for delete operations
 */
export interface DeleteResponse {
  message: string;
}
