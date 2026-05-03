from pathlib import Path
from langchain_core.documents import Document


def transform_chunks_into_docs(
    chunks: list[str], file_path: Path, file_name: str, content_type: str
):
    metadata = {
        "file_path": str(file_path),
        "file_name": file_name,
        "content_type": content_type,
    }

    return [Document(page_content=chunk, metadata=metadata) for chunk in chunks]
