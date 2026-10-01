
from .providers.base import VectorDatabase
from .providers.qdrant import QdrantAdapter

class VectorDBFactory:
    @staticmethod
    def get_database(db_type: str, **kwargs) -> VectorDatabase:
        
        db_type = db_type.lower()
        
        registry = {
            'qdrant':QdrantAdapter
        }

        db_class = registry.get(db_type, None)

        if db_class is None:
            raise ValueError(f"Unknown database provider: {db_type}")

        return db_class(**kwargs)
