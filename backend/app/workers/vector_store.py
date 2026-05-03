import os
from pathlib import Path
from functools import lru_cache
from pymupdf4llm import to_markdown
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownTextSplitter
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.exc import ProgrammingError

def extract_text(file_path: Path, content_type: str):
    if content_type == "text/plain":
        return file_path.read_text(encoding="utf-8")

    return str(to_markdown(file_path))

def chunk_text(extracted_text: str, content_type: str):
    if content_type == "text/plain":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
        )
    else:
        splitter = MarkdownTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
        )

    return splitter.split_text(extracted_text)

VECTORDB_URL = os.getenv("VECTORDB_URL", "")
VECTOR_SIZE = 768

@lru_cache(maxsize=1)
def _get_engine():
    return PGEngine.from_connection_string(VECTORDB_URL)

@lru_cache(maxsize=1)
def _get_embedding():
    return DeterministicFakeEmbedding(size=VECTOR_SIZE)

def init_db():
    try:
        _get_engine().init_vectorstore_table(
            table_name="documents",
            vector_size=VECTOR_SIZE,
        )
    except ProgrammingError:
        pass

def get_vector_store():
    return PGVectorStore.create_sync(
        engine=_get_engine(),
        table_name="documents",
        embedding_service=_get_embedding(),
    )

def store_chunks(chunks: list[str], file_path: Path, file_name: str, content_type: str):
    metadata = {
        "file_path": str(file_path),
        "file_name": file_name,
        "content_type": content_type
    }

    documents = [
        Document(
            page_content=chunk,
            metadata=metadata
        )

        for chunk in chunks 
    ]

    get_vector_store().add_documents(documents)

    return len(documents)

def process_file(file_path: Path, file_name: str, content_type: str):
    extracted_text = extract_text(
        file_path,
        content_type
    )

    chunks = chunk_text(
        extracted_text,
        content_type
    )

    count = store_chunks(
        chunks,
        file_path,
        file_name,
        content_type
    )

    return {
        "filename": file_name,
        "total_chunks": count,
        "status": "File processed"
    }
