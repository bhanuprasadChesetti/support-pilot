from app.config import settings
from .factory import VectorDBFactory
from ..ingestion.embeddings.service import get_embedding_model

def get_vector_store(
    db_name = None,
    **kwargs
):
    if db_name is None:
        db_name = settings.VECTOR_DB_NAME
    
    if not kwargs:
        # emb_mdl_service = get_embedding_model()
        kwargs = {
            "url":settings.VECTOR_DB_ENDPOINT,
            "collection_name":settings.VECTOR_DB_COLLECTION_NAME
        }
    
    vector_db = VectorDBFactory.get_database(db_name)
    
    return vector_db.get_vector_store(**kwargs)



def create_collection(
    db_name = None,
    **kwargs
):
    if db_name is None:
        db_name = settings.VECTOR_DB_NAME
    
    if not kwargs:
        kwargs = {
            "url":settings.VECTOR_DB_ENDPOINT,
            "collection_name":settings.VECTOR_DB_COLLECTION_NAME,
            "vetcor_params":{
                "dim": settings.COLLECTION_DIMENSION,
                "distance": settings.VECTOR_DISTANCE
            }
        }
    
    vector_db = VectorDBFactory.get_database(db_name)
    vector_db.create_collection(**kwargs)