"use client"

import { ReactNode } from "react"

interface CanvasLayoutProps {
  chatPanel: ReactNode
  artifactPanel: ReactNode
}

export function CanvasLayout({ chatPanel, artifactPanel }: CanvasLayoutProps) {
  return (
    <div className="flex h-screen w-full">
      {/* Chat Panel (Left) - 1/3 width */}
      <div className="flex-[0_0_33.333%] min-w-[25%] max-w-[50%] flex flex-col border-r">
        {chatPanel}
      </div>
      
      {/* Artifact Panel (Right) - 2/3 width */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {artifactPanel}
      </div>
    </div>
  )
}
