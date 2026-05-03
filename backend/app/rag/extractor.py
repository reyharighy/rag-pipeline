from pathlib import Path
from pymupdf4llm import to_markdown

def extract_text(file_path: Path, content_type: str):
    if content_type == "text/plain":
        return file_path.read_text(encoding="utf-8")

    return str(to_markdown(file_path))
