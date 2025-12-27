"use client"

import { useEffect, useRef, useState } from "react"
import { useCreateBlockNote } from "@blocknote/react"
import { BlockNoteView } from "@blocknote/shadcn"
import "@blocknote/shadcn/style.css"
import { Loader2 } from "lucide-react"
import { ArtifactContextMenu } from "./ArtifactContextMenu"
import { useCanvasOptional } from "@/contexts/CanvasContext"
import { SelectedText } from "@/types/canvas"

interface TextRendererProps {
  markdown: string
  isStreaming: boolean
  onUpdate: (newMarkdown: string) => void
  onChatWithAgentClick?: (text: string) => void
  onSelectionChange?: (selection: SelectedText | null) => void
  isPartialUpdating?: boolean
}

export function TextRenderer({ 
  markdown, 
  isStreaming, 
  onUpdate, 
  onChatWithAgentClick,
  onSelectionChange,
  isPartialUpdating 
}: TextRendererProps) {
  const editor = useCreateBlockNote()
  const isUpdatingRef = useRef(false)
  const lastMarkdownRef = useRef<string>("")
  const containerRef = useRef<HTMLDivElement>(null)
  
  // Use optional canvas context (may be null if not in CanvasProvider)
  const canvasContext = useCanvasOptional()
  const chatInputRef = canvasContext?.chatInputRef
  const setSelectedTextForChat = canvasContext?.setSelectedTextForChat
  
  // Context menu state
  const [showContextMenu, setShowContextMenu] = useState(false)
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 })
  const [selectedText, setSelectedText] = useState("")
  const mousePositionRef = useRef({ x: 0, y: 0 })
  const previousSelectionRef = useRef<any>(null)
  
  // Track mouse position during selection
  useEffect(() => {
    const handleMouseDown = (e: MouseEvent) => {
      mousePositionRef.current = { x: e.clientX, y: e.clientY }
    }
    
    document.addEventListener('mousedown', handleMouseDown)
    return () => {
      document.removeEventListener('mousedown', handleMouseDown)
    }
  }, [])
  
  // Parse markdown to blocks when markdown changes
  useEffect(() => {
    if (markdown && markdown !== lastMarkdownRef.current && !isUpdatingRef.current) {
      isUpdatingRef.current = true
      lastMarkdownRef.current = markdown
      
      try {
        const blocks = editor.tryParseMarkdownToBlocks(markdown)
        editor.replaceBlocks(editor.document, blocks)
      } finally {
        // Reset flag after a brief delay to allow editor to settle
        setTimeout(() => {
          isUpdatingRef.current = false
        }, 50)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [markdown])
  
  const handleChange = async () => {
    if (!isStreaming && !isUpdatingRef.current) {
      const fullMarkdown = await editor.blocksToMarkdownLossy(editor.document)
      if (fullMarkdown !== lastMarkdownRef.current) {
        lastMarkdownRef.current = fullMarkdown
        onUpdate(fullMarkdown)
      }
    }
  }
  
  // Handle text selection to show context menu and report to parent
  useEffect(() => {
    const handleSelection = () => {
      if (!containerRef.current) return
      
      const selection = window.getSelection()
      const text = selection?.toString().trim()
      
      if (text && text.length > 0) {
        setSelectedText(text)
        
        // Report selection to parent (for partial updates)
        if (onSelectionChange) {
          // Calculate position based on the actual markdown content, not DOM
          // The selected text needs to be found in the source markdown
          const selectedText = text
          
          // Find the position in the original markdown
          const markdownIndex = markdown.indexOf(selectedText)
          
          if (markdownIndex !== -1) {
            // Found exact match - use these positions
            onSelectionChange({
              start: markdownIndex,
              end: markdownIndex + selectedText.length,
              text: selectedText
            })
          } else {
            // If exact match not found, try to find it by removing markdown formatting
            // This handles cases where headers/bold/italic affect the DOM rendering
            // We need to search more intelligently in the markdown
            
            // Simple approach: search for the text in markdown with some tolerance
            // for whitespace differences
            const normalizedSelected = selectedText.replace(/\s+/g, ' ').trim()
            let bestMatch = -1
            let bestMatchLength = 0
            
            // Search through the markdown for the best match
            for (let i = 0; i < markdown.length; i++) {
              const remainingMarkdown = markdown.substring(i)
              // Extract plain text from this position
              const plainText = remainingMarkdown
                .replace(/^#+\s+/gm, '') // Remove headers
                .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold
                .replace(/\*([^*]+)\*/g, '$1') // Remove italic
                .replace(/`([^`]+)`/g, '$1') // Remove inline code
              
              const normalized = plainText.substring(0, selectedText.length * 2)
                .replace(/\s+/g, ' ').trim()
              
              if (normalized.startsWith(normalizedSelected)) {
                // Find the actual end position in markdown
                let charCount = 0
                let endPos = i
                const targetLength = selectedText.length
                
                while (charCount < targetLength && endPos < markdown.length) {
                  const char = markdown[endPos]
                  // Skip markdown formatting characters
                  if (char !== '#' && char !== '*' && char !== '`' && 
                      char !== '[' && char !== ']' && char !== '(' && char !== ')') {
                    charCount++
                  }
                  endPos++
                }
                
                bestMatch = i
                bestMatchLength = endPos - i
                break
              }
            }
            
            if (bestMatch !== -1) {
              onSelectionChange({
                start: bestMatch,
                end: bestMatch + bestMatchLength,
                text: markdown.substring(bestMatch, bestMatch + bestMatchLength)
              })
            } else {
              // Fallback: use DOM-based calculation as last resort
              const range = selection?.getRangeAt(0)
              if (range && containerRef.current) {
                const preSelectionRange = range.cloneRange()
                preSelectionRange.selectNodeContents(containerRef.current)
                preSelectionRange.setEnd(range.startContainer, range.startOffset)
                const start = preSelectionRange.toString().length
                
                onSelectionChange({
                  start,
                  end: start + selectedText.length,
                  text: selectedText
                })
              }
            }
          }
        }
        
        // Use the mouse position where selection started
        setMenuPosition({
          x: mousePositionRef.current.x,
          y: mousePositionRef.current.y
        })
        setShowContextMenu(true)
      } else {
        setShowContextMenu(false)
        if (onSelectionChange) {
          onSelectionChange(null)
        }
      }
    }
    
    document.addEventListener('selectionchange', handleSelection)
    
    return () => {
      document.removeEventListener('selectionchange', handleSelection)
    }
  }, [markdown, onSelectionChange])
  
  const handleChatWithAgent = (text: string) => {
    // Remove all previous yellow highlights from the entire document
    try {
      editor.forEachBlock((block) => {
        if (block.content && Array.isArray(block.content)) {
          // Check if any content has yellow background
          const hasYellowHighlight = block.content.some((c: any) => 
            c.styles?.backgroundColor === "yellow"
          )
          
          if (hasYellowHighlight) {
            // Create updated content without yellow background
            const updatedContent = block.content.map((c: any) => {
              if (c.styles?.backgroundColor === "yellow") {
                const { backgroundColor, ...restStyles } = c.styles
                return { ...c, styles: restStyles }
              }
              return c
            })
            editor.updateBlock(block, { content: updatedContent })
          }
        }
        return true // Continue traversal
      })
    } catch (e) {
      console.warn('Could not remove previous highlights:', e)
    }
    
    // Add highlight by applying yellow background to current selection
    try {
      // Apply yellow background to the selected text
      editor.addStyles({ backgroundColor: "yellow" })
    } catch (e) {
      console.warn('Could not highlight selection:', e)
    }
    
    // Close menu
    setShowContextMenu(false)
    
    // Note: We don't need to set selectedTextForChat here
    // The selection is already set by onSelectionChange callback
    // This preserves the full SelectedText object with start/end positions
    
    // Clear selection first to avoid focus conflicts
    setTimeout(() => {
      window.getSelection()?.removeAllRanges()
    }, 50)
    
    // Focus chat input after a slight delay to ensure selection is cleared
    setTimeout(() => {
      if (chatInputRef?.current) {
        chatInputRef.current.focus()
      }
    }, 150)
    
    // Call callback if provided (for backward compatibility)
    if (onChatWithAgentClick) {
      onChatWithAgentClick(text)
    }
  }
  
  const handleCloseMenu = () => {
    setShowContextMenu(false)
  }
  
  return (
    <div 
      ref={containerRef} 
      className="relative h-full w-full overflow-auto"
      onContextMenu={(e) => {
        // Disable default right-click context menu
        e.preventDefault();
      }}
    >
      {isStreaming && (
        <div className="absolute top-6 right-6 z-10 bg-blue-500 text-white px-3 py-1 rounded-full text-xs flex items-center gap-2">
          <Loader2 className="h-3 w-3 animate-spin" />
          Generating...
        </div>
      )}
      
      {isPartialUpdating && (
        <div className="absolute top-6 right-6 z-10 bg-purple-500 text-white px-3 py-1 rounded-full text-xs flex items-center gap-2">
          <Loader2 className="h-3 w-3 animate-spin" />
          Updating selection...
        </div>
      )}
      
      <div className="p-4">
        <BlockNoteView
          editor={editor}
          onChange={handleChange}
          editable={!isStreaming && !isPartialUpdating}
          theme="light"
          formattingToolbar={false}
        />
      </div>
      
      {showContextMenu && selectedText && (
        <ArtifactContextMenu
          selectedText={selectedText}
          position={menuPosition}
          onChatWithAgent={handleChatWithAgent}
          onClose={handleCloseMenu}
        />
      )}
    </div>
  )
}
