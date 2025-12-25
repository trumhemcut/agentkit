"use client"

import { createContext, useContext, useState, useCallback, ReactNode, RefObject } from "react"
import { Artifact } from "@/types/canvas"
import { ChatInputRef } from "@/components/ChatInput"
import { StorageService } from "@/services/storage"

interface CanvasContextValue {
  artifact: Artifact | undefined
  setArtifact: (artifact: Artifact | undefined) => void
  artifactId: string | null
  setArtifactId: (id: string | null) => void
  loadArtifactById: (artifactId: string, threadId: string) => boolean
  isArtifactStreaming: boolean
  setIsArtifactStreaming: (streaming: boolean) => void
  streamingContent: string
  appendStreamingContent: (delta: string) => void
  clearStreamingContent: () => void
  updateArtifactContent: (content: string) => void
  chatInputRef: RefObject<ChatInputRef | null> | null
  setChatInputRef: (ref: RefObject<ChatInputRef | null>) => void
  selectedTextForChat: string | null
  setSelectedTextForChat: (text: string | null) => void
  // Partial update state
  isPartialUpdateActive: boolean
  partialUpdateBuffer: string
  partialUpdateSelection: { start: number; end: number } | null
  startPartialUpdate: (selection: { start: number; end: number }) => void
  appendPartialUpdateChunk: (chunk: string) => void
  completePartialUpdate: () => void
}

const CanvasContext = createContext<CanvasContextValue | null>(null)

export function CanvasProvider({ children }: { children: ReactNode }) {
  const [artifact, setArtifact] = useState<Artifact | undefined>(undefined)
  const [artifactId, setArtifactId] = useState<string | null>(null)
  const [isArtifactStreaming, setIsArtifactStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const [chatInputRef, setChatInputRefState] = useState<RefObject<ChatInputRef | null> | null>(null)
  const [selectedTextForChat, setSelectedTextForChat] = useState<string | null>(null)
  
  // Partial update state
  const [isPartialUpdateActive, setIsPartialUpdateActive] = useState(false)
  const [partialUpdateBuffer, setPartialUpdateBuffer] = useState("")
  const [partialUpdateSelection, setPartialUpdateSelection] = useState<{ start: number; end: number } | null>(null)
  
  const appendStreamingContent = useCallback((delta: string) => {
    setStreamingContent(prev => prev + delta)
  }, [])
  
  const clearStreamingContent = useCallback(() => {
    setStreamingContent("")
  }, [])
  
  const setChatInputRef = useCallback((ref: RefObject<ChatInputRef | null>) => {
    setChatInputRefState(ref)
  }, [])
  
  const updateArtifactContent = useCallback((content: string) => {
    setArtifact(prev => {
      if (!prev) return undefined
      return { ...prev, content }
    })
  }, [])
  
  const startPartialUpdate = useCallback((selection: { start: number; end: number }) => {
    console.log('[CanvasContext] Starting partial update:', selection)
    setIsPartialUpdateActive(true)
    setPartialUpdateBuffer("")
    setPartialUpdateSelection(selection)
  }, [])
  
  const appendPartialUpdateChunk = useCallback((chunk: string) => {
    console.log('[CanvasContext] Appending partial update chunk:', chunk)
    setPartialUpdateBuffer(prev => prev + chunk)
  }, [])
  
  const completePartialUpdate = useCallback(() => {
    console.log('[CanvasContext] Completing partial update')
    if (!partialUpdateSelection || !artifact) {
      console.warn('[CanvasContext] Cannot complete partial update: missing selection or artifact')
      return
    }
    
    // Merge the partial update into the artifact content
    const { start, end } = partialUpdateSelection
    const newContent = 
      artifact.content.substring(0, start) +
      partialUpdateBuffer +
      artifact.content.substring(end)
    
    console.log('[CanvasContext] Merged content length:', newContent.length)
    updateArtifactContent(newContent)
    
    // Reset partial update state
    setIsPartialUpdateActive(false)
    setPartialUpdateBuffer("")
    setPartialUpdateSelection(null)
  }, [partialUpdateSelection, artifact, partialUpdateBuffer, updateArtifactContent])
  
  /**
   * Load an artifact by looking up a message with the given artifactId from storage
   * Returns true if artifact was found and loaded, false otherwise
   */
  const loadArtifactById = useCallback((artifactId: string, threadId: string): boolean => {
    console.log('[CanvasContext] loadArtifactById:', artifactId, 'threadId:', threadId);
    
    // Get the thread from storage
    const thread = StorageService.getThread(threadId);
    if (!thread) {
      console.warn('[CanvasContext] Thread not found:', threadId);
      return false;
    }
    
    // Find the message with matching artifactId
    const artifactMessage = thread.messages.find(msg => msg.artifactId === artifactId);
    if (!artifactMessage) {
      console.warn('[CanvasContext] Artifact message not found with artifactId:', artifactId);
      return false;
    }
    
    console.log('[CanvasContext] Found artifact message:', artifactMessage.id);
    
    // Update artifactId in context
    setArtifactId(artifactId);
    
    return true;
  }, [])
  
  return (
    <CanvasContext.Provider
      value={{
        artifact,
        setArtifact,
        artifactId,
        setArtifactId,
        loadArtifactById,
        isArtifactStreaming,
        setIsArtifactStreaming,
        streamingContent,
        appendStreamingContent,
        clearStreamingContent,
        updateArtifactContent,
        chatInputRef,
        setChatInputRef,
        selectedTextForChat,
        setSelectedTextForChat,
        isPartialUpdateActive,
        partialUpdateBuffer,
        partialUpdateSelection,
        startPartialUpdate,
        appendPartialUpdateChunk,
        completePartialUpdate,
      }}
    >
      {children}
    </CanvasContext.Provider>
  )
}

export function useCanvas() {
  const context = useContext(CanvasContext)
  if (!context) {
    throw new Error("useCanvas must be used within CanvasProvider")
  }
  return context
}

export function useCanvasOptional() {
  return useContext(CanvasContext)
}
