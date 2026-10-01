from app.config import settings
from .factory import EmbeddingModelFactory

def get_embedding_model(
    provider: str = None,
    model_name:str = None,
    model_kwargs:dict = None,
    encode_kwargs:dict = None
):

    provider = provider or settings.EMBEDDING_MODEL_PROVIDER
    model_name = model_name or settings.EMBEDDING_MODEL
    model_kwargs = model_kwargs or settings.EMBEDDING_MODEL_KWARGS
    encode_kwargs = encode_kwargs or settings.EMBEDDING_MODEL_ENCODE_KWARGS

    embedding_model = EmbeddingModelFactory.get_embedding_model(
        provider=provider,
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    return embedding_model