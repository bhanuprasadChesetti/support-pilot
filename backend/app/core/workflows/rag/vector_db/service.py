from app.config import settings
from .factory import VectorDBFactory
from ..ingestion.embeddings.service import get_embedding_model

def get_db_client(
    db_name = None,
    **kwargs
):
    if db_name is None:
        db_name = settings.VECTOR_DB_NAME
    
    if not kwargs:
        emb_mdl_service = get_embedding_model()
        kwargs = {
            "url":settings.VECTOR_DB_ENDPOINT,
            "collection_name":settings.VECTOR_DB_COLLECTION_NAME,
            "distance":settings.VECTOR_DISTANCE,
        }
    
    return VectorDBFactory.get_database(db_name, **kwargs)


