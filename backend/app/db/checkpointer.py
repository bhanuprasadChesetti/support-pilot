# app/core/checkpoint.py
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.config import settings

class CheckpointerManager:
    def __init__(self):
        self.pool = None
        self.saver = None


    def get_clean_conninfo(self,raw_url: str) -> str:
        """
        Workaround Utility: Strips out SQLAlchemy/asyncpg dialact prefixes 
        (e.g., 'postgresql+asyncpg://' or 'postgresql+psycopg2://') 
        so that psycopg_pool can cleanly read it as a standard Postgres URI.
        """
        if not raw_url:
            raise ValueError("Database connection URL is empty or not set in configuration.")
        
        # If the URL contains an explicit dialect driver mapping (separated by '+')
        if "+" in raw_url.split("://")[0]:
            scheme, rest = raw_url.split("://", 1)
            base_scheme = scheme.split("+")[0]  # Extracts just 'postgresql' or 'postgres'
            normalized_url = f"{base_scheme}://{rest}"
            return normalized_url
            
        return raw_url

    async def initialize(self):
        """Initializes the database pool and prepares the saver exactly once."""
        # 1. Create the persistent connection pool
        self.pool = AsyncConnectionPool(
            conninfo=self.get_clean_conninfo(settings.SYNC_DATABASE_URL),
            min_size=2,
            max_size=20,
            open=False,
            kwargs={"autocommit": True, "row_factory": dict_row} # Crucial for LangGraph
        )
        await self.pool.open()
        
        # 2. Bind it to the saver and run system setup
        self.saver = AsyncPostgresSaver(self.pool)
        await self.saver.setup()
        return self.saver

    async def close(self):
        """Clean shutdown execution."""
        if self.pool:
            await self.pool.close()


db_checkpointer = CheckpointerManager()
