/**
 * Simplified Artifact structure
 * Contains only essential fields: artifact_id, title, and content
 */
export interface Artifact {
  artifact_id: string
  title: string
  content: string
}

export interface SelectedText {
  start: number
  end: number
  text: string
}

export interface CanvasMessage {
  message: string
  artifact?: Artifact
  selectedText?: SelectedText
  action?: "create" | "update" | "rewrite" | "chat"
}

export interface CanvasEventData {
  type: "artifact_created" | "artifact_streaming" | "artifact_streaming_start" | "artifact_updated"
  artifact?: Artifact
  contentDelta?: string
  timestamp: string
}
