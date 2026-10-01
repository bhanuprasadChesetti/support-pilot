from abc import ABC
from langchain_core.documents import Document


class VectorDatabase(ABC):

    def add_documents(self, documents: list[Document]) -> None:
        self.vector_store.add_documents(documents=documents)

    def similarity_search(self,query:str,k=3):
        return self.vector_store.similarity_search(query=query, k=k)

    async def asimilarity_search(self,query:str,k=3):
        return await self.vector_store.asimilarity_search(query=query, k=k)

    def get_retriever(self,*args,**kwargs):
        return self.vector_store.as_retriever(*args,**kwargs)

    def get_underlying_vector_store(self):
        return self.vector_store


    
    


