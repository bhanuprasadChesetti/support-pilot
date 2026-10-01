
from .base import EmbeddingService
from langchain_huggingface import HuggingFaceEmbeddings





class HuggingFaceEmbeddingService(EmbeddingService):
    """
    Implementation of EmbeddingService using HuggingFaceEmbeddings.
    """

    def __init__(
        self,
        model_name:str = None,
        model_kwargs:dict = None,
        encode_kwargs:dict = None
    ):
        self.model_name = model_name or "BAAI/bge-base-en-v1.5"

        self.model_kwargs = model_kwargs 

        self.encode_kwargs = encode_kwargs or {
            "normalize_embeddings": True  # CRUCIAL: Pre-normalizes vectors for Dot Product speed
        }

        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs=self.model_kwargs,
            encode_kwargs=self.encode_kwargs
        )

