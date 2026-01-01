"use client"

import React, { useState, useEffect } from "react"
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
  InputOTPSeparator,
} from "@/components/ui/input-otp"
import { Button } from "@/components/ui/button"
import { REGEXP_ONLY_DIGITS_AND_CHARS, REGEXP_ONLY_DIGITS } from "input-otp"
import { useA2UIStore } from "@/stores/a2uiStore"
import { resolvePath } from "@/types/a2ui"
import { a2uiManager } from "@/lib/a2ui/A2UIManager"

interface A2UIOTPInputProps {
  id: string
  props: {
    title?: { literalString?: string; path?: string }
    description?: { literalString?: string; path?: string }
    maxLength?: number
    groups?: Array<{ start: number; end: number }>
    patternType?: "digits" | "alphanumeric"
    buttonText?: { literalString?: string; path?: string }
    action?: {
      name: string
      context?: Record<string, any>
    }
    disabled?: boolean
    value?: { path?: string }
  }
  dataModel: Record<string, any>
  surfaceId: string
  onAction?: (actionName: string, context: Record<string, any>) => void
}

export const A2UIOTPInput: React.FC<A2UIOTPInputProps> = ({
  id,
  props,
  dataModel,
  surfaceId,
  onAction,
}) => {
  const updateDataModel = useA2UIStore((state) => state.updateDataModel)
  
  // Resolve text properties
  const title = props.title?.literalString || resolvePath(dataModel, props.title?.path) || "Enter verification code"
  const description = props.description?.literalString || resolvePath(dataModel, props.description?.path) || "Please enter the verification code sent to your device."
  const buttonText = props.buttonText?.literalString || resolvePath(dataModel, props.buttonText?.path) || "Verify"
  
  // Resolve value from data model
  const dataModelValue = resolvePath(dataModel, props.value?.path) || ""
  const [otpValue, setOtpValue] = useState(dataModelValue)
  
  // Configuration
  const maxLength = props.maxLength || 6
  const groups = props.groups || [{ start: 0, end: maxLength }]
  const patternType = props.patternType || "digits"
  const disabled = props.disabled || false
  
  // Sync with data model changes
  useEffect(() => {
    if (dataModelValue !== otpValue) {
      setOtpValue(dataModelValue)
    }
  }, [dataModelValue])
  
  const handleChange = (value: string) => {
    setOtpValue(value)
    
    if (props.value?.path) {
      // Extract key from path (e.g., "/ui/otp-input-abc/value" → "value")
      const pathParts = props.value.path.split("/").filter((p) => p)
      const key = pathParts[pathParts.length - 1]
      const parentPath = "/" + pathParts.slice(0, -1).join("/")
      
      // Update data model
      updateDataModel(surfaceId, parentPath, [
        { key, valueString: value }
      ])
    }
  }
  
  const handleSubmit = () => {
    console.log('[A2UIOTPInput] Submit button clicked', {
      id,
      surfaceId,
      otpValue,
      action: props.action
    })
    
    // New A2UI v0.9 pattern: use action from props
    if (props.action) {
      console.log('[A2UIOTPInput] Using a2uiManager with action:', props.action.name)
      a2uiManager.handleComponentAction(
        surfaceId,
        id,
        props.action.name,
        props.action.context || {}
      )
    } 
    // Legacy support: fallback to onAction callback
    else if (onAction) {
      console.log('[A2UIOTPInput] Using legacy onAction callback')
      onAction("otp_submit", {
        componentId: id,
        value: otpValue,
        path: props.value?.path,
      })
    }
    else {
      console.warn('[A2UIOTPInput] No action defined for OTP submit button')
    }
  }
  
  // Select pattern based on type
  const pattern =
    patternType === "alphanumeric"
      ? REGEXP_ONLY_DIGITS_AND_CHARS
      : REGEXP_ONLY_DIGITS
  
  // Render slot groups with separators
  const renderGroups = () => {
    return groups.map((group, groupIndex) => {
      const slots = []
      for (let i = group.start; i < group.end; i++) {
        slots.push(<InputOTPSlot key={i} index={i} />)
      }
      
      return (
        <React.Fragment key={groupIndex}>
          <InputOTPGroup>{slots}</InputOTPGroup>
          {groupIndex < groups.length - 1 && <InputOTPSeparator />}
        </React.Fragment>
      )
    })
  }
  
  return (
    <div className="flex flex-col items-center space-y-6 p-8 border rounded-lg bg-card">
      {/* Title */}
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground max-w-md">
          {description}
        </p>
      </div>
      
      {/* OTP Input */}
      <InputOTP
        maxLength={maxLength}
        value={otpValue}
        onChange={handleChange}
        pattern={pattern}
        disabled={disabled}
      >
        {renderGroups()}
      </InputOTP>
      
      {/* Value Display */}
      <div className="text-center text-sm text-muted-foreground">
        {otpValue === "" ? (
          <>Enter your verification code</>
        ) : (
          <>
            Entered: <span className="font-mono font-semibold">{otpValue}</span>
          </>
        )}
      </div>
      
      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={disabled || otpValue.length < maxLength}
        className="w-full max-w-xs"
      >
        {buttonText}
      </Button>
    </div>
  )
}
