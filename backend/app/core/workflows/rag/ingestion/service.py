import logging
from langchain_core.indexing import index
from langchain_classic.indexes import SQLRecordManager
from app.config import settings
from .preprocessor import DirectoryPreProcessor
from .parsers.text import load_text_files_from_directory
from .chunkers.markdown import MarkdownSplitter
from .chunkers.recursive_char import RecursiveCharacterTextSplitter
from ..vector_db.service import get_vector_store

logger = logging.getLogger(__name__)

# 1. Setup Postgres Record Manager (Replace with your actual database credentials)
POSTGRES_CONN_STRING = settings.SYNC_DATABASE_URL

record_manager = SQLRecordManager(
    namespace=f"{settings.VECTOR_DB_NAME}/{settings.VECTOR_DB_COLLECTION_NAME}", 
    db_url=POSTGRES_CONN_STRING
)

logger.info(f"Using Record Manager with namespace: {record_manager.namespace}")
# Automatically creates the internal tracking table if it doesn't exist
record_manager.create_schema()


vector_store = get_vector_store()


def preprocess_docs(source_dir:str,target_dir:str=None,ftype = None):
    
    logger.info(f"Source directory: {source_dir}")

    target_directory = DirectoryPreProcessor.preprocess(
        source_dir=source_dir,
        target_dir=target_dir,
        ftype = ftype    
    )
 
    logger.info(f"Target directory: {target_directory}")

    return target_directory


def load_documents(
    target_directory:str,
    chunk_size:int=1000,
    chunk_overlap:int=100,
    glob:str="**/*.md"
):

    logger.info(f"Target directory: {target_directory}")

    files_data = load_text_files_from_directory(
        target_directory,
        glob=glob
    )

    no_of_files = len(files_data)
    logger.info(f"No of Files found: {no_of_files}")

    chunks = []

    markdown_splitter = MarkdownSplitter()
    recursive_char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    for i,file in enumerate(files_data):
        logger.info(f"File {i+1}/{no_of_files}")
        file_splitted_docs = markdown_splitter.split(file)
        file_chunks = recursive_char_splitter.split_documents(file_splitted_docs)
        chunks.extend(file_chunks)

    no_of_chunks = len(chunks)
    logger.info(f"Number of Chunks found: {no_of_chunks}")

    indexing_result = index(
        docs_source=chunks,
        record_manager=record_manager,
        vector_store=vector_store,
        cleanup="incremental",  # Deletes old chunks of modified files, skips unchanged files
        source_id_key="source"  # Tracks identity based on the file path in metadata
    )

    logger.info('Ingestion Completed')

