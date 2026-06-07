import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file's raw bytes.
    
    Uses PyMuPDF for reliable text extraction from all pages.
    """
    text_parts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()
