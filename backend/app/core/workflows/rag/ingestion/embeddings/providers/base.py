from abc import ABC



class EmbeddingService(ABC):
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> list[float]:
        return self.embeddings.embed_query(query)

    def get_underlying_model(self):
        return self.embeddings
    

