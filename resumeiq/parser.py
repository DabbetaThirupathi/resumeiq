"""Extract plain text from uploaded resume files (PDF, DOCX, TXT)."""

import io
import os

from pypdf import PdfReader
from docx import Document

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class UnsupportedFileError(ValueError):
    """Raised when an uploaded file type is not supported."""


def extension_of(filename):
    return os.path.splitext(filename or "")[1].lower()


def extract_text(filename, data):
    """Return text from the file bytes ``data`` based on the filename extension."""
    ext = extension_of(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileError(f"Unsupported file type '{ext or 'none'}'. Use PDF, DOCX or TXT.")

    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    if ext == ".docx":
        document = Document(io.BytesIO(data))
        parts = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                parts.append(" ".join(cell.text for cell in row.cells))
        return "\n".join(parts)

    return data.decode("utf-8", errors="ignore")
