from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService, chat_service

router = APIRouter()


def get_chat_service() -> ChatService:
    """Dependency provider for ChatService."""
    return chat_service


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def send_chat_message(
    request: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    """Chat endpoint for receiving customer messages and returning AI support responses."""
    return await service.get_response(request)
