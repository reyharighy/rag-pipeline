from pathlib import Path

from app.rag import extract_text, chunk_text, store_chunks


def process_file(file_path: Path, file_name: str, content_type: str):
    extracted_text = extract_text(file_path, content_type)
    chunks = chunk_text(extracted_text, content_type)
    count = store_chunks(chunks, file_path, file_name, content_type)

    return {"filename": file_name, "total_chunks": count, "status": "File processed"}
