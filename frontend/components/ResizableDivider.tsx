"use client";

import { useEffect, useRef, useState } from 'react';
import { GripVertical } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ResizableDividerProps {
  onResize: (leftWidth: number) => void;
  minLeftWidth?: number;
  maxLeftWidth?: number;
  initialLeftWidth?: number;
  className?: string;
}

/**
 * ResizableDivider component
 * 
 * A draggable vertical divider that allows users to resize panels.
 * Emits resize events with the new left panel width percentage.
 */
export function ResizableDivider({
  onResize,
  minLeftWidth = 20,
  maxLeftWidth = 70,
  initialLeftWidth = 33.33,
  className,
}: ResizableDividerProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const container = containerRef.current?.parentElement;
      if (!container) return;

      const containerRect = container.getBoundingClientRect();
      const mouseX = e.clientX - containerRect.left;
      const containerWidth = containerRect.width;
      
      // Calculate percentage
      let leftWidthPercent = (mouseX / containerWidth) * 100;
      
      // Clamp between min and max
      leftWidthPercent = Math.max(minLeftWidth, Math.min(maxLeftWidth, leftWidthPercent));
      
      onResize(leftWidthPercent);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    // Set cursor style during drag
    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, minLeftWidth, maxLeftWidth, onResize]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative flex items-center justify-center w-1 hover:bg-primary/10 transition-colors cursor-ew-resize group flex-shrink-0",
        isDragging && "bg-primary/20",
        className
      )}
      onMouseDown={handleMouseDown}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    />
  );
}
