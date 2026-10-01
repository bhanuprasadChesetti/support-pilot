from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore

from qdrant_client import models
from qdrant_client.models import Distance
from .base import VectorDatabase


class QdrantAdapter(VectorDatabase):

    def resovle_distance(self,distance):
        registry = {
            "dot": Distance.DOT,
            "cosine": Distance.COSINE,
            "euclidean": Distance.EUCLID
        }

        return registry.get(distance, Distance.DOT)

    def __init__(self, url: str,collection_name:str,embedding_model, distance):
        self.client = QdrantClient(url=url) 
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.distance = self.resovle_distance(distance)
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embedding_model,
            distance=self.distance
        )


    def create_collection(
        self,
        collection_name:str,
        vetcor_params:dict
    ):
        """
        Creates a new collection in Qdrant.
        
        Args:
            collection_name (str): The name of the collection to create.
            vetcor_params (dict): A dictionary containing vector parameters.
                - dim (int): The dimension of the vectors.
                - distance (Distance): The distance metric to use.
        """
        
        if self.client.collection_exists(collection_name):
            return
        
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    distance= vetcor_params.get("distance") or Distance.DOT,
                    size= vetcor_params.get("dim") or 768
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            }
        )
        
        


