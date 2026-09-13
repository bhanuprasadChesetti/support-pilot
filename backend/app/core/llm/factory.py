from .constants import Providers
from langchain.chat_models.base import init_chat_model
from app.config import settings



class LLMFactory:

    @staticmethod
    def get_model(
        provider: str = settings.DEFAULT_LLM_PROVIDER,
        model: str = settings.DEFAULT_LLM_MODEL,
        temperature: float = settings.DEFAULT_LLM_TEMPERATURE,
        timeout: float = getattr(settings, "DEFAULT_LLM_TIMEOUT", 120.0),
    ):

        """
        Initializes a chat model from LangChain.

        Args:
            provider: LLM Provider
            model: LLM Model Name
            temperature: Temperature for the model
            timeout: Network/socket timeout limit in seconds
        Returns:
            Initialized chat model instance
        
        Example:
            >>> llm = LLMFactory.get_model(provider="openai", model="gpt-3.5-turbo", timeout=120.0)
        """

        if provider not in Providers:
            raise ValueError(f"Provider {provider} is not supported. Supported providers are: {','.join([p for p in Providers])}")
            
        llm = init_chat_model(
            model=model,
            model_provider=provider,
            temperature=temperature,
            timeout=timeout
        )

        return llm
