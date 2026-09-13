import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.conversations.enums import ChatStatus


class ConversationResponse(BaseModel):
    id: str = Field(..., description="Public UUID of the conversation")
    title: Optional[str] = Field(None, description="Conversation title or topic summary")
    last_message: Optional[str] = Field(None, description="Preview of the last message in the conversation")
    timestamp: str = Field(..., description="Formatted timestamp or relative time string")
    status: ChatStatus = Field(ChatStatus.OPEN, description="Status of the chat session")


class ConversationMessageResponse(BaseModel):
    id: str = Field(..., description="Message ID")
    sender: str = Field(..., description="Sender role: customer or ai")
    text: str = Field(..., description="Message content text")
    timestamp: str = Field(..., description="Formatted timestamp")


class CreateConversationResponse(BaseModel):
    id: str = Field(..., description="Public UUID of the newly created conversation")
    title: str = Field(..., description="Initial conversation title")
    last_message: str = Field("Chat started", description="Last message summary")
    timestamp: str = Field("Just now", description="Formatted timestamp")
