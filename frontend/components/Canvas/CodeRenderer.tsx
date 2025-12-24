"use client"

import { useEffect, useState } from "react"
import CodeMirror from "@uiw/react-codemirror"
import { javascript } from "@codemirror/lang-javascript"
import { python } from "@codemirror/lang-python"
import { html } from "@codemirror/lang-html"
import { css } from "@codemirror/lang-css"
import { json } from "@codemirror/lang-json"
import { Loader2 } from "lucide-react"

interface CodeRendererProps {
  code: string
  language: string
  isStreaming: boolean
  onUpdate: (newCode: string) => void
}

export function CodeRenderer({ code, language, isStreaming, onUpdate }: CodeRendererProps) {
  const [localCode, setLocalCode] = useState(code)
  
  // Update local code when prop changes
  useEffect(() => {
    setLocalCode(code)
  }, [code])
  
  const extensions = getLanguageExtension(language)
  
  const handleChange = (value: string) => {
    setLocalCode(value)
    if (!isStreaming) {
      onUpdate(value)
    }
  }
  
  return (
    <div className="relative h-full w-full">
      {isStreaming && (
        <div className="absolute top-2 right-2 z-10 bg-blue-500 text-white px-3 py-1 rounded-full text-xs flex items-center gap-2">
          <Loader2 className="h-3 w-3 animate-spin" />
          Generating...
        </div>
      )}
      
      <CodeMirror
        value={localCode}
        extensions={extensions}
        onChange={handleChange}
        editable={!isStreaming}
        className="text-sm"
        height="100%"
        theme="light"
      />
    </div>
  )
}

function getLanguageExtension(language: string) {
  const languageMap: Record<string, any> = {
    javascript: javascript({ jsx: true }),
    js: javascript({ jsx: true }),
    jsx: javascript({ jsx: true }),
    typescript: javascript({ jsx: true, typescript: true }),
    ts: javascript({ jsx: true, typescript: true }),
    tsx: javascript({ jsx: true, typescript: true }),
    python: python(),
    py: python(),
    html: html(),
    css: css(),
    json: json(),
  }
  
  return [languageMap[language.toLowerCase()] || javascript()]
}
