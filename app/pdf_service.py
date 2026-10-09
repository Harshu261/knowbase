from pathlib import Path
from pypdf import PdfReader

def extract_text(file_path:str)->str:
    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages)
