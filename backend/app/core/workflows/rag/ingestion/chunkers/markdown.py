
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from .base import BaseSplitter



class MarkdownSplitter(BaseSplitter):
    
    def __init__(
        self,
        headers_to_split_on:list[tuple[str,str]] = [("#", "Header 1"),("##", "Header 2")]
    ):
        self.headers_to_split_on = headers_to_split_on
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False
        )
    
    def split(self,document:Document)->list[Document]:

        chunks = self.splitter.split_text(document.page_content)
        
        for chunk in chunks:
            chunk.metadata = {**document.metadata, **chunk.metadata}
            
        return chunks

    

