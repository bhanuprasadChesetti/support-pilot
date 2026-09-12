import uuid
from typing import List, Optional

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.conversations.enums import ChatStatus, MediaType, MessageRole
from app.db.base import Base
from app.db.mixins import IDMixin, SoftDeleteMixin, TimestampMixin


class Conversation(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "conversations"

    # Public ID used in API/UI URLs
    public_id: Mapped[uuid.UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[ChatStatus] = mapped_column(
        Enum(ChatStatus),
        default=ChatStatus.OPEN,
        nullable=False,
        index=True,
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Browser / OS / language / country context
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
    )

    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at.asc()",
    )


class ChatMessage(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_messages"

    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            name="chat_role_enum",
            native_enum=True,
        ),
        nullable=False,
    )

    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    tool_calls: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    media: Mapped[List["ChatMedia"]] = relationship(
        "ChatMedia",
        back_populates="message",
        cascade="all, delete-orphan",
    )


class ChatMedia(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_media"

    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "chat_messages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    media_type: Mapped[MediaType] = mapped_column(
        Enum(
            MediaType,
            name="media_type_enum",
            native_enum=True,
        ),
        nullable=False,
    )

    storage_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    # Relationship
    message: Mapped["ChatMessage"] = relationship(
        "ChatMessage",
        back_populates="media",
    )