"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat completion request model."""
    model: str = Field(default="openai/gpt-3.5-turbo", description="AI model to use")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stream: Optional[bool] = Field(default=False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat completion response model."""
    id: str = Field(..., description="Response ID")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Response choices")
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage information")


class ModelInfo(BaseModel):
    """AI model information."""
    id: str = Field(..., description="Model ID")
    name: Optional[str] = Field(default=None, description="Model display name")
    description: Optional[str] = Field(default=None, description="Model description")
    pricing: Optional[Dict[str, Any]] = Field(default=None, description="Pricing information")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="Application version")
    message: Optional[str] = Field(default=None, description="Additional status message")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    detail: Optional[str] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class RootResponse(BaseModel):
    """Root endpoint response model."""
    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="Application version")
    docs: str = Field(..., description="Documentation URL")
    health: str = Field(..., description="Health check URL")
