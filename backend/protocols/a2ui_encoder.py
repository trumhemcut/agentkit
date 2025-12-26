"""
A2UI Protocol Message Encoder

This module provides encoding functionality for A2UI messages to be sent via
SSE (Server-Sent Events) or JSONL (JSON Lines) formats.

The encoder handles:
- Converting Pydantic A2UI models to JSON strings
- Formatting messages for SSE protocol (data: prefix, double newline)
- Formatting messages for JSONL protocol (single line JSON with newline)

Usage:
    from protocols.a2ui_encoder import A2UIEncoder
    from protocols.a2ui_types import SurfaceUpdate, Component
    
    encoder = A2UIEncoder()
    
    # Create A2UI message
    surface_update = SurfaceUpdate(
        surface_id="surface-123",
        components=[
            Component(id="checkbox-1", component={"Checkbox": {...}})
        ]
    )
    
    # Encode for SSE
    sse_message = encoder.encode(surface_update)
    # Returns: "data: {...}\n\n"
    
    # Encode for JSONL
    jsonl_message = encoder.encode_jsonl(surface_update)
    # Returns: "{...}\n"
"""

import json
from typing import Union
from .a2ui_types import (
    A2UIMessage,
    SurfaceUpdate,
    DataModelUpdate,
    BeginRendering,
    DeleteSurface
)


class A2UIEncoder:
    """
    Encoder for A2UI protocol messages.
    
    Converts A2UI Pydantic models to SSE or JSONL formatted strings for streaming.
    """
    
    def __init__(self):
        """Initialize the A2UI encoder."""
        pass
    
    def encode(self, message: A2UIMessage) -> str:
        """
        Encode A2UI message to SSE (Server-Sent Events) format.
        
        SSE format follows the EventStream specification:
        - Lines starting with "data: " contain the message payload
        - Messages end with double newline (\n\n)
        
        Args:
            message: A2UI message (SurfaceUpdate, DataModelUpdate, BeginRendering, or DeleteSurface)
        
        Returns:
            SSE-formatted string: "data: {json}\n\n"
        
        Example:
            >>> encoder = A2UIEncoder()
            >>> msg = SurfaceUpdate(surface_id="test", components=[])
            >>> encoded = encoder.encode(msg)
            >>> print(encoded)
            data: {"type":"surfaceUpdate","surfaceId":"test","components":[]}
            
        """
        # Use model_dump_json with by_alias=True to ensure camelCase field names
        json_str = message.model_dump_json(by_alias=True, exclude_none=True)
        return f"data: {json_str}\n\n"
    
    def encode_jsonl(self, message: A2UIMessage) -> str:
        """
        Encode A2UI message to JSONL (JSON Lines) format.
        
        JSONL format is newline-delimited JSON:
        - Each message is a single line of JSON
        - Lines end with newline (\n)
        
        Args:
            message: A2UI message (SurfaceUpdate, DataModelUpdate, BeginRendering, or DeleteSurface)
        
        Returns:
            JSONL string: "{json}\n"
        
        Example:
            >>> encoder = A2UIEncoder()
            >>> msg = BeginRendering(surface_id="test", root_component_id="root")
            >>> encoded = encoder.encode_jsonl(msg)
            >>> print(encoded)
            {"type":"beginRendering","surfaceId":"test","rootComponentId":"root"}
            
        """
        json_str = message.model_dump_json(by_alias=True, exclude_none=True)
        return f"{json_str}\n"
    
    def encode_dict(self, message: A2UIMessage) -> dict:
        """
        Convert A2UI message to dictionary.
        
        Useful for logging, debugging, or when JSON serialization
        is handled by another component.
        
        Args:
            message: A2UI message
        
        Returns:
            Dictionary representation with camelCase keys
        """
        return message.model_dump(by_alias=True, exclude_none=True)
    
    def encode_batch(self, messages: list[A2UIMessage], format: str = "sse") -> str:
        """
        Encode multiple A2UI messages in batch.
        
        Args:
            messages: List of A2UI messages to encode
            format: Output format - "sse" or "jsonl"
        
        Returns:
            Concatenated encoded messages
        
        Raises:
            ValueError: If format is not "sse" or "jsonl"
        """
        if format == "sse":
            return "".join(self.encode(msg) for msg in messages)
        elif format == "jsonl":
            return "".join(self.encode_jsonl(msg) for msg in messages)
        else:
            raise ValueError(f"Unknown format: {format}. Use 'sse' or 'jsonl'.")


def is_a2ui_message(data: dict) -> bool:
    """
    Check if a dictionary represents an A2UI message.
    
    A2UI messages are identified by their 'type' field which must be one of:
    - surfaceUpdate
    - dataModelUpdate
    - beginRendering
    - deleteSurface
    
    Args:
        data: Dictionary to check
    
    Returns:
        True if data is an A2UI message, False otherwise
    
    Example:
        >>> is_a2ui_message({"type": "surfaceUpdate", "surfaceId": "test"})
        True
        >>> is_a2ui_message({"type": "TEXT_MESSAGE_CONTENT", "delta": "hello"})
        False
    """
    return data.get("type") in [
        "surfaceUpdate",
        "dataModelUpdate",
        "beginRendering",
        "deleteSurface"
    ]
