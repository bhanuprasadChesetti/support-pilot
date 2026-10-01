from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    PyMuPDFLoader
)
from langchain_docling.loader import DoclingLoader
from .base import Loader

class PDFLoader(Loader):
    
    def validate(self,file_path:str):
        self.check_file_exists(file_path)
        self.check_is_pdf(file_path)
    
    def load(self,file_path:str,loader_type:str='docling')->Document:
        self.validate(file_path)

        loader = {
            'pypdf':self.pypdf,
            'pymupdf':self.pymupdf,
            'docling':self.docling,
        }
        
        if loader_type not in loader:
            raise ValueError(f"Invalid loader type: {loader_type}")
        
        documents = loader[loader_type](file_path)

        filtered_documents = []

        for page in documents:
            if len(page.page_content.strip())<50:
                continue
            filtered_documents.append(page)
        
        return filtered_documents
    
    
    def pypdf(self,file_path:str)->Document:
        loader = PyPDFLoader(file_path)
        return loader.load()

    def pymupdf(self,file_path:str)->Document:
        loader = PyMuPDFLoader(file_path)
        return loader.load()
    
    def docling(self,file_path:str)->Document:
        loader = DoclingLoader(file_path=file_path)
        # Load all documents
        return loader.load()
