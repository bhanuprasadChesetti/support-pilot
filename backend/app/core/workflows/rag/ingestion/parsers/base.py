from abc import ABC
import os

class Loader(ABC):

    def check_file_exists(self,file_path:str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Path not found: {file_path}")
    
    def check_is_directory(self,directory_path:str):
        if not os.path.isdir(directory_path):
            raise ValueError(f"Path is not a directory: {directory_path}")

    def check_is_pdf(self,file_path:str):
        return file_path.endswith(".pdf")
    
    def check_is_text(self,file_path:str):
        return file_path.endswith(".txt")
    

