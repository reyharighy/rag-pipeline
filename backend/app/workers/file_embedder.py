from pathlib import Path

from app.rag import extract_text, chunk_text, transform_chunks_into_docs
from app.services import get_vector_db_service


def embed_file(file_path: Path, file_name: str, content_type: str):
    extracted_text = extract_text(file_path, content_type)
    chunks = chunk_text(extracted_text, content_type)
    documents = transform_chunks_into_docs(chunks, file_path, file_name, content_type)
    get_vector_db_service().add_documents(documents)

    return {
        "filename": file_name,
        "total_chunks": len(chunks),
        "status": "File processed",
    }
