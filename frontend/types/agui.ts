/**
 * AG-UI Protocol event types
 * 
 * These types should match the official ag-ui-protocol events from the backend
 */

// Re-export types from @ag-ui/core when available
// For now, define compatible types

export enum EventType {
  // Run lifecycle events
  RUN_STARTED = 'RUN_STARTED',
  RUN_FINISHED = 'RUN_FINISHED',
  RUN_ERROR = 'RUN_ERROR',
  
  // Text message events
  TEXT_MESSAGE_START = 'TEXT_MESSAGE_START',
  TEXT_MESSAGE_CONTENT = 'TEXT_MESSAGE_CONTENT',
  TEXT_MESSAGE_END = 'TEXT_MESSAGE_END',
  
  // Tool call events (for future use)
  TOOL_CALL_START = 'TOOL_CALL_START',
  TOOL_CALL_ARGS = 'TOOL_CALL_ARGS',
  TOOL_CALL_END = 'TOOL_CALL_END',
  TOOL_CALL_RESULT = 'TOOL_CALL_RESULT',
  
  // Additional events
  THINKING = 'THINKING',
  EXECUTING = 'EXECUTING',
  COMPLETE = 'COMPLETE',
  ERROR = 'ERROR',
  
  // Custom events (for canvas and other extensions)
  CUSTOM = 'CUSTOM',
}

export type AGUIEventType = EventType | string;

/**
 * Base event structure
 */
export interface BaseEvent {
  type: AGUIEventType;
  timestamp?: number;
}

/**
 * Run lifecycle events
 */
export interface RunStartedEvent extends BaseEvent {
  type: EventType.RUN_STARTED;
  thread_id?: string;
  run_id?: string;
}

export interface RunFinishedEvent extends BaseEvent {
  type: EventType.RUN_FINISHED;
  thread_id?: string;
  run_id?: string;
}

export interface RunErrorEvent extends BaseEvent {
  type: EventType.RUN_ERROR;
  thread_id?: string;
  run_id?: string;
  message?: string;
}

/**
 * Text message events
 */
export interface TextMessageStartEvent extends BaseEvent {
  type: EventType.TEXT_MESSAGE_START;
  message_id: string;
  role?: string;
  agentName?: string;
  metadata?: {
    message_type?: 'text' | 'artifact';
    artifact_type?: 'code' | 'text' | 'document';
    artifact_id?: string;
    language?: string;
    title?: string;
  };
}

export interface TextMessageContentEvent extends BaseEvent {
  type: EventType.TEXT_MESSAGE_CONTENT;
  message_id: string;
  delta: string;
}

export interface TextMessageEndEvent extends BaseEvent {
  type: EventType.TEXT_MESSAGE_END;
  message_id: string;
}

/**
 * Tool call events (for future use)
 */
export interface ToolCallStartEvent extends BaseEvent {
  type: EventType.TOOL_CALL_START;
  tool_call_id: string;
  tool_name: string;
  parent_message_id?: string;
}

export interface ToolCallArgsEvent extends BaseEvent {
  type: EventType.TOOL_CALL_ARGS;
  tool_call_id: string;
  args?: string;
  delta?: string;
}

export interface ToolCallEndEvent extends BaseEvent {
  type: EventType.TOOL_CALL_END;
  tool_call_id: string;
}

export interface ToolCallResultEvent extends BaseEvent {
  type: EventType.TOOL_CALL_RESULT;
  tool_call_id: string;
  content: string;
}

/**
 * Generic error event
 */
export interface ErrorEvent extends BaseEvent {
  type: EventType.ERROR;
  data?: any;
  message?: string;
}

/**
 * Custom event (for canvas and other extensions)
 */
export interface CustomEvent extends BaseEvent {
  type: EventType.CUSTOM;
  name: string;
  value: any;
}

/**
 * Union type for all AG-UI events
 */
export type AGUIEvent = 
  | RunStartedEvent
  | RunFinishedEvent
  | RunErrorEvent
  | TextMessageStartEvent
  | TextMessageContentEvent
  | TextMessageEndEvent
  | ToolCallStartEvent
  | ToolCallArgsEvent
  | ToolCallEndEvent
  | ToolCallResultEvent
  | ErrorEvent
  | CustomEvent
  | BaseEvent; // Fallback for unknown events

// AG-UI connection state
export interface ConnectionState {
  isConnected: boolean;
  error: string | null;
  lastEventTime: number | null;
}
