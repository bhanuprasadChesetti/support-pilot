import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select

from app.config import settings
from app.conversations.enums import MessageRole
from app.conversations.models import ChatMessage, Conversation
from app.users.models import User
from app.organizations.models import Organization
from app.core.llm.service import LLMService
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


from typing import List, AsyncIterator
from sqlalchemy.orm import selectinload

class ChatService:
    """Service abstraction for processing customer support chat interactions.

    Designed to decouple business logic from HTTP handling so future LLM
    integrations, streaming responses, RAG retrieval, and tool calling can be
    plugged in seamlessly without API contract breaking changes.
    """

    async def stream_response(
        self, request: ChatRequest, user_id: int, organization_id: int
    ) -> AsyncIterator[str]:
        """Generates a streaming response for a customer message, yielding SSE data lines and persisting history."""
        try:
            async with get_db() as db:
                conversation_id_str = request.conversation_id
                conversation = None

                if conversation_id_str:
                    try:
                        conv_uuid = uuid.UUID(conversation_id_str)
                        stmt = select(Conversation).where(Conversation.public_id == conv_uuid)
                        result = await db.execute(stmt)
                        conversation = result.scalars().first()
                    except ValueError:
                        conversation = None

                if not conversation:
                    conv_uuid = uuid.uuid4()
                    conversation_id_str = str(conv_uuid)
                    conversation = Conversation(
                        public_id=conv_uuid,
                        organization_id=organization_id,
                        user_id=user_id,
                        title=request.message[:40] if request.message else "Support Chat",
                    )
                    db.add(conversation)
                    await db.flush()
                elif not conversation.title and request.message:
                    conversation.title = request.message[:40]

                user_message = ChatMessage(
                    conversation_id=conversation.id,
                    role=MessageRole.USER,
                    content=request.message,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(user_message)
                await db.flush()

                # Retrieve full message history for context
                stmt_msgs = (
                    select(ChatMessage)
                    .where(ChatMessage.conversation_id == conversation.id)
                    .order_by(ChatMessage.created_at.asc())
                )
                msgs_result = await db.execute(stmt_msgs)
                history_messages = msgs_result.scalars().all()

                formatted_messages = []
                for msg in history_messages:
                    role_str = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
                    formatted_messages.append({
                        "role": role_str.lower(),
                        "content": msg.content or "",
                    })

                full_response = ""
                try:
                    async for chunk in LLMService.stream_chat_response(
                        provider=settings.DEFAULT_LLM_PROVIDER,
                        model=settings.DEFAULT_LLM_MODEL,
                        messages=formatted_messages,
                        system_prompt="You are a helpful assistant.",
                    ):
                        full_response += chunk
                        yield f"data: {chunk}\n\n"
                except Exception as e:
                    logger.error(f"Error streaming LLM response: {str(e)}")
                    fallback = "Sorry, I'm having trouble connecting right now."
                    full_response += fallback
                    yield f"data: {fallback}\n\n"

                if full_response:
                    assistant_message = ChatMessage(
                        conversation_id=conversation.id,
                        role=MessageRole.ASSISTANT,
                        content=full_response,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(assistant_message)
                    await db.flush()

        except Exception as e:
            logger.error(f"Database operation failed in ChatService.stream_response: {str(e)}", exc_info=True)
            yield "data: Failed to process chat message: INTERNAL ERROR\n\n"


    async def get_response(self, request: ChatRequest, user_id: int , organization_id: int) -> ChatResponse:
        """Generates a response for a customer message and persists the conversation history."""
        try:
            async with get_db() as db:
                conversation_id_str = request.conversation_id
                conversation = None

                if conversation_id_str:
                    try:
                        conv_uuid = uuid.UUID(conversation_id_str)
                        stmt = select(Conversation).where(Conversation.public_id == conv_uuid)
                        result = await db.execute(stmt)
                        conversation = result.scalars().first()
                    except ValueError:
                        conversation = None

                if not conversation:
                    conv_uuid = uuid.uuid4()
                    conversation_id_str = str(conv_uuid)
                    conversation = Conversation(
                        public_id=conv_uuid,
                        organization_id=organization_id,
                        user_id=user_id,
                        title=request.message[:40] if request.message else "Support Chat",
                    )
                    db.add(conversation)
                    await db.flush()
                elif not conversation.title and request.message:
                    conversation.title = request.message[:40]

                user_message = ChatMessage(
                    conversation_id=conversation.id,
                    role=MessageRole.USER,
                    content=request.message,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(user_message)
                await db.flush()

                # Retrieve full message history for context
                stmt_msgs = (
                    select(ChatMessage)
                    .where(ChatMessage.conversation_id == conversation.id)
                    .order_by(ChatMessage.created_at.asc())
                )
                msgs_result = await db.execute(stmt_msgs)
                history_messages = msgs_result.scalars().all()

                formatted_messages = []
                for msg in history_messages:
                    role_str = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
                    formatted_messages.append({
                        "role": role_str.lower(),
                        "content": msg.content or "",
                    })

                try:
                    llm_response = await LLMService.generate_chat_response(
                        provider=settings.DEFAULT_LLM_PROVIDER,
                        model=settings.DEFAULT_LLM_MODEL,
                        messages=formatted_messages,
                        system_prompt="You are a helpful assistant.",
                    )
                except Exception as e:
                    logger.error(f"Error calling LLM: {str(e)}")
                    llm_response = "Sorry, I'm having trouble connecting right now."

                assistant_message = ChatMessage(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=llm_response,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(assistant_message)
                await db.flush()

                return ChatResponse(
                    response=llm_response,
                    conversation_id=conversation_id_str,
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Database operation failed in ChatService: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process chat message: INTERNAL ERROR",
            )

    async def create_conversation(self, user_id: int, organization_id: int) -> dict:
        """Creates a new conversation record in the database."""
        try:
            async with get_db() as db:
                conv_uuid = uuid.uuid4()
                conversation = Conversation(
                    public_id=conv_uuid,
                    organization_id=organization_id,
                    user_id=user_id,
                    title="New Support Chat",
                )
                db.add(conversation)
                await db.flush()
                return {
                    "id": str(conv_uuid),
                    "title": conversation.title,
                    "last_message": "Chat started",
                    "timestamp": "Just now",
                }
        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}", exc_info=True)
            conv_uuid = uuid.uuid4()
            return {
                "id": str(conv_uuid),
                "title": "New Support Chat",
                "last_message": "Chat started",
                "timestamp": "Just now",
            }

    async def list_conversations(self, user_id: int, organization_id: int ) -> List[dict]:
        """Lists all conversations for a user/organization ordered by creation date desc."""
        try:
            async with get_db() as db:
                stmt = (
                    select(Conversation)
                    .where(Conversation.user_id == user_id, Conversation.organization_id == organization_id)
                    .options(selectinload(Conversation.messages))
                    .order_by(Conversation.created_at.desc())
                )
                result = await db.execute(stmt)
                conversations = result.scalars().all()
                out = []
                for conv in conversations:
                    last_msg_text = "No messages yet"
                    if conv.messages:
                        last_msg_text = conv.messages[-1].content or "No content"
                    out.append({
                        "id": str(conv.public_id),
                        "title": conv.title or "Support Chat",
                        "last_message": last_msg_text,
                        "timestamp": conv.created_at.strftime("%b %d, %H:%M") if conv.created_at else "Just now",
                        "status": conv.status,
                    })
                return out
        except Exception as e:
            logger.error(f"Failed to list conversations: {str(e)}", exc_info=True)
            return []

    async def get_conversation_messages(self, conversation_id_str: str, user_id: int, organization_id: int) -> List[dict]:
        """Fetches all messages for a specific conversation."""
        try:
            async with get_db() as db:
                conv_uuid = uuid.UUID(conversation_id_str)
                stmt = (
                    select(Conversation)
                    .where(
                        Conversation.public_id == conv_uuid,
                        Conversation.user_id == user_id,
                        Conversation.organization_id == organization_id
                    )
                    .options(selectinload(Conversation.messages))
                )
                result = await db.execute(stmt)
                conversation = result.scalars().first()
                if not conversation:
                    return []
                messages = []
                for msg in conversation.messages:
                    sender = "customer" if msg.role == MessageRole.USER else "ai"
                    messages.append({
                        "id": str(msg.id),
                        "sender": sender,
                        "text": msg.content or "",
                        "timestamp": msg.created_at.strftime("%H:%M %p") if msg.created_at else "",
                    })
                return messages
        except Exception as e:
            logger.error(f"Failed to fetch conversation messages: {str(e)}", exc_info=True)
            return []


# Global singleton instance for injection or simple usage
chat_service = ChatService()


