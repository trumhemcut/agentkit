// AG-UI Protocol event types
export type AGUIEventType = 
  | 'RUN_STARTED'
  | 'RUN_FINISHED'
  | 'RUN_ERROR'
  | 'TEXT_MESSAGE_START'
  | 'TEXT_MESSAGE_CONTENT'
  | 'TEXT_MESSAGE_END'
  | 'THINKING'
  | 'EXECUTING'
  | 'COMPLETE'
  | 'ERROR';

export interface AGUIEvent {
  type: AGUIEventType;
  data?: any;
  timestamp?: number;
  agentName?: string;
  threadId?: string;
  thread_id?: string;
  run_id?: string;
  message_id?: string;
  role?: string;
  delta?: string;
  message?: string;
}

// AG-UI text message chunk
export interface TextMessageChunk {
  content: string;
  isComplete: boolean;
}

// AG-UI run state
export interface RunState {
  runId: string;
  status: 'started' | 'running' | 'finished' | 'error';
  message?: string;
}

// AG-UI connection state
export interface ConnectionState {
  isConnected: boolean;
  error: string | null;
  lastEventTime: number | null;
}
