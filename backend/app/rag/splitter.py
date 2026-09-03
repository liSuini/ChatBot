"""文本分块器：基于 langchain RecursiveCharacterTextSplitter"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


def split_text(text: str) -> list[str]:
    """将长文本切分为带重叠的块"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    return splitter.split_text(text)
