"use client"

import { CodeRenderer } from "./CodeRenderer"
import { TextRenderer } from "./TextRenderer"
import { ArtifactHeader } from "./ArtifactHeader"
import { ModelSelector } from "@/components/ModelSelector"
import { ArtifactV3 } from "@/types/canvas"
import { FileText } from "lucide-react"

interface ArtifactRendererProps {
  artifact: ArtifactV3 | null
  isStreaming: boolean
  streamingContent?: string
  onArtifactUpdate: (content: string, index: number) => void
  onVersionChange: (index: number) => void
}

export function ArtifactRenderer({ 
  artifact, 
  isStreaming, 
  streamingContent = "",
  onArtifactUpdate,
  onVersionChange 
}: ArtifactRendererProps) {
  if (!artifact) {
    return <EmptyArtifactState />
  }
  
  const currentContent = artifact.contents.find(c => c.index === artifact.currentIndex)
  
  if (!currentContent) {
    return <EmptyArtifactState />
  }
  
  const handleCopy = () => {
    const content = currentContent.type === "code" 
      ? currentContent.code 
      : currentContent.fullMarkdown
    navigator.clipboard.writeText(content)
  }
  
  const handleDownload = () => {
    const content = currentContent.type === "code" 
      ? currentContent.code 
      : currentContent.fullMarkdown
    const extension = currentContent.type === "code" 
      ? currentContent.language 
      : "md"
    const blob = new Blob([content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${currentContent.title}.${extension}`
    a.click()
    URL.revokeObjectURL(url)
  }
  
  // Use streaming content if currently streaming
  const displayContent = isStreaming && streamingContent 
    ? (currentContent.type === "code" 
        ? { ...currentContent, code: streamingContent }
        : { ...currentContent, fullMarkdown: streamingContent })
    : currentContent
  
  return (
    <div className="flex flex-col h-full bg-white">
      <ArtifactHeader
        title={displayContent.title}
        currentVersion={artifact.currentIndex}
        totalVersions={artifact.contents.length}
        onVersionChange={onVersionChange}
        onCopy={handleCopy}
        onDownload={handleDownload}
      />
      
      <div className="flex-1 overflow-auto">
        {displayContent.type === "code" ? (
          <CodeRenderer
            code={displayContent.code}
            language={displayContent.language}
            isStreaming={isStreaming}
            onUpdate={(newCode) => onArtifactUpdate(newCode, artifact.currentIndex)}
          />
        ) : (
          <TextRenderer
            markdown={displayContent.fullMarkdown}
            isStreaming={isStreaming}
            onUpdate={(newMarkdown) => onArtifactUpdate(newMarkdown, artifact.currentIndex)}
          />
        )}
      </div>
    </div>
  )
}

function EmptyArtifactState() {
  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header with Model Selector */}
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <h2 className="text-lg font-semibold">Canvas</h2>
        <ModelSelector />
      </div>
      
      {/* Empty State Content */}
      <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
        <FileText className="h-16 w-16 mb-4 text-gray-300" />
        <h3 className="text-lg font-semibold mb-2">No Artifact Yet</h3>
        <p className="text-sm text-center max-w-md">
          Start a conversation and ask me to create code or text content.
          <br />
          I&apos;ll generate it here for you to view and edit.
        </p>
      </div>
    </div>
  )
}
