from .constants import Providers
from langchain.chat_models.base import init_chat_model
from app.config import settings



class LLMFactory:

    @staticmethod
    def get_model(
        provider:str = settings.DEFAULT_LLM_PROVIDER,
        model:str = settings.DEFAULT_LLM_MODEL,
        temperature:float = settings.DEFAULT_LLM_TEMPERATURE,
    ):

        """
        Initializes a chat model from LangChain.

        Args:
            provider: LLM Provider
            model_name: LLM Model Name
            temperature: Temperature for the model
        Returns:
            Initialized chat model instance
        
        Example:
            >>> llm = LLMFactory.get_model(provider="openai", model_name="gpt-3.5-turbo")
        """

        if provider not in Providers:
            raise ValueError(f"Provider {provider} is not supported. Supported providers are: {','.join([p for p in Providers])}")
            
        llm=init_chat_model(model=model,model_provider=provider,temperature=temperature)

        return llm
