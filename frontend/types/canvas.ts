export interface ArtifactContentCode {
  index: number
  type: "code"
  title: string
  code: string
  language: string
}

export interface ArtifactContentText {
  index: number
  type: "text"
  title: string
  fullMarkdown: string
}

export type ArtifactContent = ArtifactContentCode | ArtifactContentText

export interface ArtifactV3 {
  currentIndex: number
  contents: ArtifactContent[]
}

export interface SelectedText {
  start: number
  end: number
  text: string
}

export interface CanvasMessage {
  message: string
  artifact?: ArtifactV3
  selectedText?: SelectedText
  action?: "create" | "update" | "rewrite" | "chat"
}

export interface CanvasEventData {
  type: "artifact_created" | "artifact_streaming" | "artifact_streaming_start" | "artifact_updated" | "artifact_version_changed"
  artifact?: ArtifactV3
  contentDelta?: string
  artifactIndex?: number
  timestamp: string
}
