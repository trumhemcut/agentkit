"use client"

import { useState, useEffect } from "react"
import { CanvasLayout } from "@/components/Canvas/CanvasLayout"
import { ArtifactRenderer } from "@/components/Canvas/ArtifactRenderer"
import { CanvasChatContainer } from "@/components/Canvas/CanvasChatContainer"
import { CanvasProvider, useCanvas } from "@/contexts/CanvasContext"
import { getAGUIClient, setupCanvasEventHandlers } from "@/services/agui-client"
import { StorageService } from "@/services/storage"
import { v4 as uuidv4 } from "uuid"

function CanvasPageContent() {
  const { 
    artifact, 
    setArtifact, 
    isArtifactStreaming, 
    setIsArtifactStreaming,
    streamingContent,
    appendStreamingContent,
    clearStreamingContent,
    updateArtifactContent,
    changeArtifactVersion 
  } = useCanvas()
  
  const [threadId] = useState(() => {
    const id = uuidv4()
    // Initialize thread in storage
    StorageService.saveThread({
      id,
      title: 'Canvas Session',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    })
    return id
  })
  const [aguiClient] = useState(() => getAGUIClient())
  
  // Setup canvas event handlers
  useEffect(() => {
    const currentThreadId = threadId // Capture in closure
    
    const cleanup = setupCanvasEventHandlers(aguiClient, {
      onArtifactCreated: (newArtifact) => {
        console.log('[Canvas Page] Artifact created:', newArtifact)
        setArtifact(newArtifact)
        setIsArtifactStreaming(false)
        clearStreamingContent()
      },
      onArtifactStreamingStart: (newArtifact) => {
        console.log('[Canvas Page] Artifact streaming started:', newArtifact)
        setArtifact(newArtifact)
        setIsArtifactStreaming(true)
        clearStreamingContent()
      },
      onArtifactStreaming: (delta, index) => {
        console.log('[Canvas Page] Artifact streaming delta:', { delta, index })
        appendStreamingContent(delta)
      },
      onArtifactUpdated: (updatedArtifact) => {
        console.log('[Canvas Page] Artifact updated:', updatedArtifact)
        setArtifact(updatedArtifact)
        setIsArtifactStreaming(false)
        clearStreamingContent()
      },
      onVersionChanged: (updatedArtifact) => {
        console.log('[Canvas Page] Version changed:', updatedArtifact)
        setArtifact(updatedArtifact)
      },
    })
    
    return cleanup
  }, [aguiClient, setArtifact, setIsArtifactStreaming, appendStreamingContent, clearStreamingContent])
  
  return (
    <CanvasLayout
      chatPanel={
        <CanvasChatContainer threadId={threadId} />
      }
      artifactPanel={
        <ArtifactRenderer
          artifact={artifact}
          isStreaming={isArtifactStreaming}
          streamingContent={streamingContent}
          onArtifactUpdate={updateArtifactContent}
          onVersionChange={changeArtifactVersion}
        />
      }
    />
  )
}

export default function CanvasPage() {
  return (
    <CanvasProvider>
      <CanvasPageContent />
    </CanvasProvider>
  )
}
