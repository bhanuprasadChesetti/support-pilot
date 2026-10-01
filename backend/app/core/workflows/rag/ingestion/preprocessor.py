from abc import ABC
from pathlib import Path
from .parsers.docling import docling


def markdown_convertor(
    source_file_path:str|Path,
    target_file_path:str|Path = None
):
    """
    Convert a document to markdown format.

    Args:
        file_path: The path to the document to convert.

    Returns:
        The converted document in markdown format
    """
    markdown_content = docling(source_file_path)
    
    if target_file_path is None:
        source_path = Path(source_file_path)
        target_file_path = source_path.with_suffix('.md')
    
    with open(target_file_path, 'w') as f:
        f.write(markdown_content)
    
    return target_file_path




class Preprocessor(ABC):
    
    def __init__(self):
        self.supporte_file_types = {
            '.docx',
            '.pdf',
            '.pptx',
            '.html',
            '.htm',
            '.txt'
        }
        


class FilePreprocessor(Preprocessor):
    
    def preprocess(
        self,
        source_files:list[str|Path],
        target_dir:str = None,
        ftype = None
    ):

        supported_file_types  = set(ftype) if ftype else self.supporte_file_types
        
        target_dir = Path(target_dir) if target_dir else Path('.')
     

        target_files = []

        for fp in source_files:

            fp = Path(fp)

            if fp.is_dir() or fp.suffix not in supported_file_types :
                continue
            
            new_path = target_dir / f"{fp.stem}.md"

            markdown_convertor(fp,new_path)

            target_files.append(new_path) 

        return target_files
        


class DirectoryPreProcessor:

    @staticmethod
    def preprocess(
        source_dir:str,
        target_dir:str=None,
        ftype = None
    ):
        source_path = Path(source_dir)

        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_path}")

        if target_dir is None:
            target_dir = source_path.parent / f"{source_path.name}_cleaned"

        target_path = Path(target_dir)

        if not target_path.exists():
            target_path.mkdir(parents=True)

        supported_file_types  = ftype if ftype else {
            '.docx',
            '.pdf',
            '.pptx',
            '.html',
            '.htm',
            '.txt'
        }

        for fp in source_path.rglob('*'):
            if fp.is_dir() or fp.suffix not in supported_file_types :
                continue
            
            relative_path = fp.relative_to(source_path)

            new_path = target_path / relative_path.with_suffix('.md')

            new_path.parent.mkdir(parents=True, exist_ok=True)

            markdown_convertor(fp,new_path)

        return target_dir
            

        
        