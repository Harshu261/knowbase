from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
import pymupdf
import pytesseract
from PIL import Image

def extract_text(file_path:str)->str:
    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages)


def extract_pages(file_path: str) -> list[dict]:
    reader = PdfReader(file_path)
    pages = []

    # Open the PDF with PyMuPDF for rendering pages when OCR is needed.
    pdf = pymupdf.open(file_path)

    try:
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            # Scanned pages usually contain images instead of selectable text.
            if not text.strip():
                pdf_page = pdf[page_number - 1]

                # Render at 2x scale to help OCR recognize text.
                pixmap = pdf_page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2),
                    alpha=False,
                )

                image = Image.open(
                    BytesIO(pixmap.tobytes("png"))
                )

                text = pytesseract.image_to_string(image)

            if text.strip():
                pages.append({
                    "page_number": page_number,
                    "text": text.strip(),
                })
    finally:
        pdf.close()

    return pages

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            # Prefer a space near the end, but don't make
            # chunks unnecessarily small.
            boundary = text.rfind(" ", start, end)

            if boundary > start + chunk_size // 2:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = end - overlap

        # If no useful boundary exists, preserve fixed-size
        # progress. Otherwise, start after a space.
        if next_start > 0 and not text[next_start - 1].isspace():
            boundary = text.find(" ", next_start, end)

            if boundary != -1:
                next_start = boundary + 1

        if next_start <= start:
            next_start = start + step

        start = next_start

    return chunks

def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[dict]:
    chunks = []
    chunk_index = 0

    for page in pages:
        page_chunks = chunk_text(
            page["text"],
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for chunk in page_chunks:
            chunks.append({
                "chunk_index": chunk_index,
                "page_number": page["page_number"],
                "content": chunk,
            })
            chunk_index += 1

    return chunks
