"use client"

import { useEffect, useMemo, useRef } from "react"
import { useCreateBlockNote } from "@blocknote/react"
import { BlockNoteView } from "@blocknote/shadcn"
import "@blocknote/shadcn/style.css"
import { Loader2 } from "lucide-react"

interface TextRendererProps {
  markdown: string
  isStreaming: boolean
  onUpdate: (newMarkdown: string) => void
}

export function TextRenderer({ markdown, isStreaming, onUpdate }: TextRendererProps) {
  const editor = useCreateBlockNote()
  const isUpdatingRef = useRef(false)
  const lastMarkdownRef = useRef<string>("")
  
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
  
  return (
    <div className="relative h-full w-full overflow-auto">
      {isStreaming && (
        <div className="absolute top-6 right-6 z-10 bg-blue-500 text-white px-3 py-1 rounded-full text-xs flex items-center gap-2">
          <Loader2 className="h-3 w-3 animate-spin" />
          Generating...
        </div>
      )}
      
      <div className="p-4">
        <BlockNoteView
          editor={editor}
          onChange={handleChange}
          editable={!isStreaming}
          theme="light"
        />
      </div>
    </div>
  )
}
