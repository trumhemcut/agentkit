"use client"

import { createContext, useContext, useState, useCallback, ReactNode, RefObject } from "react"
import { ArtifactV3, ArtifactContentCode, ArtifactContentText } from "@/types/canvas"
import { ChatInputRef } from "@/components/ChatInput"

interface CanvasContextValue {
  artifact: ArtifactV3 | null
  setArtifact: (artifact: ArtifactV3 | null) => void
  isArtifactStreaming: boolean
  setIsArtifactStreaming: (streaming: boolean) => void
  streamingContent: string
  appendStreamingContent: (delta: string) => void
  clearStreamingContent: () => void
  updateArtifactContent: (content: string, index: number) => void
  changeArtifactVersion: (index: number) => void
  chatInputRef: RefObject<ChatInputRef | null> | null
  setChatInputRef: (ref: RefObject<ChatInputRef | null>) => void
  selectedTextForChat: string | null
  setSelectedTextForChat: (text: string | null) => void
}

const CanvasContext = createContext<CanvasContextValue | null>(null)

export function CanvasProvider({ children }: { children: ReactNode }) {
  const [artifact, setArtifact] = useState<ArtifactV3 | null>(null)
  const [isArtifactStreaming, setIsArtifactStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const [chatInputRef, setChatInputRefState] = useState<RefObject<ChatInputRef | null> | null>(null)
  const [selectedTextForChat, setSelectedTextForChat] = useState<string | null>(null)
  
  const appendStreamingContent = useCallback((delta: string) => {
    setStreamingContent(prev => prev + delta)
  }, [])
  
  const clearStreamingContent = useCallback(() => {
    setStreamingContent("")
  }, [])
  
  const setChatInputRef = useCallback((ref: RefObject<ChatInputRef | null>) => {
    setChatInputRefState(ref)
  }, [])
  
  const updateArtifactContent = useCallback((content: string, index: number) => {
    setArtifact(prev => {
      if (!prev) return null
      
      const updatedContents = prev.contents.map(c => {
        if (c.index === index) {
          if (c.type === "code") {
            return { ...c, code: content } as ArtifactContentCode
          } else {
            return { ...c, fullMarkdown: content } as ArtifactContentText
          }
        }
        return c
      })
      
      return { ...prev, contents: updatedContents }
    })
  }, [])
  
  const changeArtifactVersion = useCallback((index: number) => {
    setArtifact(prev => {
      if (!prev) return null
      return { ...prev, currentIndex: index }
    })
  }, [])
  
  return (
    <CanvasContext.Provider
      value={{
        artifact,
        setArtifact,
        isArtifactStreaming,
        setIsArtifactStreaming,
        streamingContent,
        appendStreamingContent,
        clearStreamingContent,
        updateArtifactContent,
        changeArtifactVersion,
        chatInputRef,
        setChatInputRef,
        selectedTextForChat,
        setSelectedTextForChat,
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
