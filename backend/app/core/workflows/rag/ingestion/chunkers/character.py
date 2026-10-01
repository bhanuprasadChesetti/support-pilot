from langchain_core.documents import Document
from langchain_text_splitters import (
    CharacterTextSplitter as _CharacterTextSplitter
)

from .base import BaseSplitter

class CharacterTextSplitter(BaseSplitter):

    def __init__(
        self,
        chunk_size:int,
        chunk_overlap:int,
        separator:str = "\n",
        chunk_size_calulator=len
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        self.chunk_size_calulator = chunk_size_calulator
        
        self.splitter = _CharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self.chunk_size_calulator,
            separator=self.separator,
        )

    
    def split(
        self,
        document: Document
    )->list[str]:
        return self.splitter.split_text(document.page_content)


    def split_documents(
        self,
        documents:list[Document]
    )->list[Document]:
        return self.splitter.split_documents(documents)