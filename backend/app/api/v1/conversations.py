from typing import Annotated, List

from fastapi import APIRouter, Depends

from app.schemas.conversations import (
    ConversationMessageResponse,
    ConversationResponse,
    CreateConversationResponse,
)
from app.services.chat_service import ChatService, chat_service

router = APIRouter()


def get_chat_service() -> ChatService:
    """Dependency provider for ChatService."""
    return chat_service


@router.get("/conversations", response_model=List[ConversationResponse], tags=["Conversations"])
async def get_conversations(
    service: Annotated[ChatService, Depends(get_chat_service)],
    user_id: int,
    organization_id: int,
) -> List[ConversationResponse]:
    """Retrieve all conversations for the user/organization."""
    return await service.list_conversations(user_id=user_id, organization_id=organization_id)


@router.post("/conversations", response_model=CreateConversationResponse, tags=["Conversations"])
async def create_new_conversation(
    service: Annotated[ChatService, Depends(get_chat_service)],
    user_id: int,
    organization_id: int,
) -> CreateConversationResponse:
    """Create a new conversation session."""
    return await service.create_conversation(user_id=user_id, organization_id=organization_id)


@router.get("/conversations/{conversation_id}/messages", response_model=List[ConversationMessageResponse], tags=["Conversations"])
async def get_conversation_messages(
    conversation_id: str,
    service: Annotated[ChatService, Depends(get_chat_service)],
    user_id: int,
    organization_id: int,
) -> List[ConversationMessageResponse]:
    """Retrieve all messages for a specific conversation session."""
    return await service.get_conversation_messages(conversation_id, user_id=user_id, organization_id=organization_id)

