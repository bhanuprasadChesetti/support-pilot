from docling.document_converter import DocumentConverter

def docling(file_path:str):
    """
    Load a document using Docling.

    Args:
        file_path: The path to the document to load.

    Returns:
        The loaded document in markdown format
    """
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()