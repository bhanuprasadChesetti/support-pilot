import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader 
from langchain_community.document_loaders import DirectoryLoader



def load_text_file(
    file_path: str,
    encoding: str = "utf-8"
) -> Document:

    """Load a single text file using TextLoader."""
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    loader = TextLoader(file_path, encoding=encoding)
    document = loader.load()
    return document[0]


def load_text_files_from_directory(
    directory_path: str,
    glob: str = "**/*.txt",
    encoding: str = "utf-8"
) -> List[Document]:

    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Path not found: {directory_path}")

    if not os.path.isdir(directory_path):
        raise ValueError(f"Path is not a directory: {directory_path}")

    dir_loader = DirectoryLoader(
        directory_path,
        glob=glob,
        loader_cls=TextLoader,
        loader_kwargs={
            "encoding": encoding
        }
    )


    return dir_loader.load()






    
    
