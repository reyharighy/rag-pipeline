from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
)


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
