
from .providers.hugging_face import HuggingFaceEmbeddingService

class EmbeddingModelFactory:
    @staticmethod
    def get_embedding_model(
        provider :str,
        model_name:str = None,
        model_kwargs:dict = None,
        encode_kwargs:dict = None
    ):

        provider_registry = {
            "huggingface":HuggingFaceEmbeddingService
        }

        if provider not in provider_registry:
            raise ValueError(f'Provider {provider} is not supported. Supported providers are {provider_registry.keys()}')

        provider = provider_registry[provider]

        embedding_model = provider(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

        return embedding_model
    
