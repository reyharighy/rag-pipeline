from pathlib import Path
from langchain_core.documents import Document

from app.services import get_vector_db_service


def store_chunks(chunks: list[str], file_path: Path, file_name: str, content_type: str):
    metadata = {
        "file_path": str(file_path),
        "file_name": file_name,
        "content_type": content_type,
    }

    documents = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

    get_vector_db_service().add_documents(documents)

    return len(documents)
