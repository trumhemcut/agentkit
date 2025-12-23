"use client"

import { Button } from "@/components/ui/button"
import { ModelSelector } from "@/components/ModelSelector"
import { ChevronLeft, ChevronRight, Download, Copy } from "lucide-react"

interface ArtifactHeaderProps {
  title?: string
  currentVersion: number
  totalVersions: number
  onVersionChange: (version: number) => void
  onDownload?: () => void
  onCopy?: () => void
}

export function ArtifactHeader({ 
  title, 
  currentVersion, 
  totalVersions, 
  onVersionChange,
  onDownload,
  onCopy
}: ArtifactHeaderProps) {
  const canGoPrevious = currentVersion > 1
  const canGoNext = currentVersion < totalVersions
  
  return (
    <div className="flex items-center justify-between p-4 border-b bg-white">
      <h2 className="text-lg font-semibold truncate flex-1">{title || "Untitled"}</h2>
      
      <div className="flex items-center gap-2">
        {/* Model Selector */}
        <ModelSelector />
        
        {/* Action Buttons */}
        {onCopy && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onCopy}
            title="Copy to clipboard"
          >
            <Copy className="h-4 w-4" />
          </Button>
        )}
        
        {onDownload && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onDownload}
            title="Download"
          >
            <Download className="h-4 w-4" />
          </Button>
        )}
        
        {/* Version Navigation */}
        {totalVersions > 1 && (
          <div className="flex items-center gap-1 ml-2 border-l pl-2">
            <Button
              variant="ghost"
              size="icon"
              disabled={!canGoPrevious}
              onClick={() => onVersionChange(currentVersion - 1)}
              title="Previous version"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            
            <span className="text-sm text-gray-600 min-w-[50px] text-center">
              {currentVersion} / {totalVersions}
            </span>
            
            <Button
              variant="ghost"
              size="icon"
              disabled={!canGoNext}
              onClick={() => onVersionChange(currentVersion + 1)}
              title="Next version"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
