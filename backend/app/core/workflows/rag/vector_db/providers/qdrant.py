import os
import logging
from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import Distance
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_qdrant import (
    FastEmbedSparse,
    QdrantVectorStore,
    RetrievalMode
)
from .base import VectorDatabase

logger = logging.getLogger(__name__)


class QdrantAdapter(VectorDatabase):

    def resovle_distance(self,distance):
        registry = {
            "dot": Distance.DOT,
            "cosine": Distance.COSINE,
            "euclidean": Distance.EUCLID
        }

        return registry.get(distance, Distance.DOT)

    def __init__(self):

        self.dense_embedding_model_name = os.getenv("EMBEDDING_MODEL")
        self.sparse_embedding_model_name = os.getenv("SPARSE_EMBEDDING_MODEL")

        if self.dense_embedding_model_name is None:
            raise ValueError("EMBEDDING_MODEL is not set")
        
        if self.sparse_embedding_model_name is None:
            raise ValueError("SPARSE_EMBEDDING_MODEL is not set")
        

    
    def get_client(self,url):
        if not hasattr(self,"client"):
            self.client = QdrantClient(url=url)
        return self.client


    def get_vector_store(
        self, 
        url: str,
        collection_name:str
    ):
    
        self.client = self.get_client(url) 
        self.collection_name = collection_name


        # 1. Setup Client-Side Embedding Generators
        dense_embeddings = FastEmbedEmbeddings(
            model_name= self.dense_embedding_model_name
        )

        # 2. Setup Client-Side Sparse Embeddings (BM25/SPLADE via FastEmbed)
        sparse_embeddings = FastEmbedSparse(
            model_name= self.sparse_embedding_model_name
        )

        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=dense_embeddings,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse",
            distance=Distance.DOT
        )

        return self.vector_store

    def create_collection(
        self,
        url: str,
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

        client = self.get_client(url)
        
        if client.collection_exists(collection_name):
            return


        distance = self.resovle_distance(vetcor_params.get("distance"))
        dimension = vetcor_params.get("dim")

        logger.info(f"Creating collection with distance: {distance} and dimension: {dimension}")
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    distance= distance,
                    size= dimension
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            }
        )

        