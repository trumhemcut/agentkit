import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Generate a unique ID with timestamp and random suffix
 * Ensures uniqueness even when called multiple times in the same millisecond
 */
let idCounter = 0;
export function generateUniqueId(prefix: string = 'id'): string {
  const timestamp = Date.now();
  const counter = idCounter++;
  const random = Math.random().toString(36).substring(2, 9);
  return `${prefix}-${timestamp}-${counter}-${random}`;
}
