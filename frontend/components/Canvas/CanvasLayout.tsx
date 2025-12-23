"use client"

import { ReactNode } from "react"

interface CanvasLayoutProps {
  chatPanel: ReactNode
  artifactPanel: ReactNode
}

export function CanvasLayout({ chatPanel, artifactPanel }: CanvasLayoutProps) {
  return (
    <div className="flex h-screen w-full">
      {/* Chat Panel (Left) - 40% width */}
      <div className="flex-[0_0_40%] min-w-[30%] max-w-[60%] flex flex-col border-r">
        {chatPanel}
      </div>
      
      {/* Artifact Panel (Right) - 60% width */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {artifactPanel}
      </div>
    </div>
  )
}
