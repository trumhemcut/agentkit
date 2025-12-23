"use client"

import { useCallback, useRef } from "react"
import { useCanvas } from "@/contexts/CanvasContext"
import { useModelSelection } from "@/hooks/useModelSelection"
import { sendCanvasMessage } from "@/services/api"
import { getAGUIClient } from "@/services/agui-client"
import { Message } from "@/types/chat"
import { v4 as uuidv4 } from "uuid"

/**
 * Hook for sending canvas messages
 * Integrates with the canvas context and AGUI client
 */
export function useCanvasChat(threadId: string) {
  const { artifact } = useCanvas()
  const { selectedModel } = useModelSelection()
  const aguiClientRef = useRef(getAGUIClient())
  
  const sendMessage = useCallback(async (messages: Message[]) => {
    const runId = uuidv4()
    
    console.log('[useCanvasChat] Sending message with artifact:', artifact)
    
    // Convert chat messages to API format
    const apiMessages = messages.map(msg => ({
      role: msg.role,
      content: msg.content
    }))
    
    // Send canvas message and process events through AGUI client
    await sendCanvasMessage(
      apiMessages,
      threadId,
      runId,
      artifact || undefined,
      undefined, // selectedText - can be added later
      undefined, // action - let backend determine
      selectedModel || undefined,
      (event) => {
        aguiClientRef.current.processEvent(event)
      }
    )
  }, [threadId, artifact, selectedModel])
  
  return { sendMessage }
}
