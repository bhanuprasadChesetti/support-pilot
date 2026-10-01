from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter as _RecursiveCharacterTextSplitter
)
from .base import BaseSplitter


class RecursiveCharacterTextSplitter(BaseSplitter):

    def __init__(
        self,
        chunk_size:int,
        chunk_overlap:int,
        separators:list[str]=[" \n\n", "\n", ".", " "],
        chunk_size_calulator=len
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators
        self.chunk_size_calulator = chunk_size_calulator
        
        self.splitter = _RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self.chunk_size_calulator,
            separators=self.separators,
        )

    def split(
        self,
        document: Document 
    )-> list[str]:
        return self.splitter.split_text(document.page_content)


    def split_documents(
        self,
        documents:list[Document]
    )->list[Document]:
        return self.splitter.split_documents(documents)


