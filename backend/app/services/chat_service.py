from app.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    """Service abstraction for processing customer support chat interactions.

    Designed to decouple business logic from HTTP handling so future LLM
    integrations, streaming responses, RAG retrieval, and tool calling can be
    plugged in seamlessly without API contract breaking changes.
    """

    async def get_response(self, request: ChatRequest) -> ChatResponse:
        """Generates a response for a customer message.

        In Phase 1, this returns a deterministic mock response.
        """
        mock_reply = (
            "I understand your concern. Could you please provide your order "
            "number so I can help you further?"
        )
        return ChatResponse(response=mock_reply)


# Global singleton instance for injection or simple usage
chat_service = ChatService()
