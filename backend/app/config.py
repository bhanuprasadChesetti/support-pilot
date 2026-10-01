import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl

# 1. Load into os.environ first
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "SupportPilot API"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    DEFAULT_LLM_PROVIDER: str 
    DEFAULT_LLM_MODEL: str 
    DEFAULT_LLM_TEMPERATURE: float = 0
    DEFAULT_LLM_TIMEOUT: float = 120.0
    NVIDIA_API_KEY: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str


    EMBEDDING_MODEL_PROVIDER:str
    EMBEDDING_MODEL:str
    SPARSE_EMBEDDING_MODEL:str
    EMBEDDING_MODEL_KWARGS:dict
    EMBEDDING_MODEL_ENCODE_KWARGS:dict

    VECTOR_DB_NAME:str
    VECTOR_DB_ENDPOINT:str
    VECTOR_DB_COLLECTION_NAME:str
    COLLECTION_DIMENSION:int
    VECTOR_DISTANCE:str


    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    
    @computed_field
    @property
    def SYNC_DATABASE_URL(self) -> str:
        # Formats the string specifically for LangChain's SQLRecordManager using psycopg2
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


    # 2. Pydantic will now automatically see them in os.environ
    model_config = SettingsConfigDict(
        extra="ignore",
    )

settings = Settings()
