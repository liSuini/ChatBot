"""文档解析器：支持 PDF / DOCX / TXT / MD"""

from pathlib import Path

from app.core.exceptions import ChatBotException

# 文件类型白名单
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def parse_file(file_path: str, file_type: str) -> str:
    """根据文件类型解析提取纯文本"""
    ext = f".{file_type.lower()}"
    if ext not in ALLOWED_EXTENSIONS:
        raise ChatBotException("BAD_REQUEST", f"不支持的文件类型: {ext}", 400)

    if ext == ".pdf":
        return _parse_pdf(file_path)
    if ext == ".docx":
        return _parse_docx(file_path)
    # txt / md
    return _parse_text(file_path)


def _parse_pdf(file_path: str) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts).strip()


def _parse_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parts)


def _parse_text(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")
