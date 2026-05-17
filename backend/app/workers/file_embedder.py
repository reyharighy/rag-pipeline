from pathlib import Path
from app.rag import extract_text, chunk_text, transform_chunks_into_docs

from app.config import get_settings
from app.database.tables import VectorDocument

_embedding_cfg = get_settings().embedding

def embed_file_and_store(
    file_path: Path, file_name: str, content_type: str, _file_size: int
):
    extracted_text = extract_text(file_path, content_type)
    chunks = chunk_text(extracted_text, content_type)
    documents = transform_chunks_into_docs(chunks, file_path, file_name, content_type)

    try:
        vector_document = VectorDocument(_embedding_cfg.service)
        vector_document.add(entry=documents)
    except Exception as e:
        print(f"[FILE EMBEDDER] Failed to embed and store file: {e}")

        return {
            "chunks": len(chunks),
            "result": {
                "status": "error",
                "message": "Failed to embed and store file",
            },
        }

    print(f"[FILE EMBEDDER] File embedded and stored successfully")

    return {
        "chunks": len(chunks),
        "result": {
            "status": "success",
            "message": "File embedded and stored successfully",
        },
    }
