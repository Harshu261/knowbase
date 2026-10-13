
from app import pdf_service
import pytest

from app.pdf_service import chunk_text, chunk_pages


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakeReader:
    def __init__(self, file_path):
        self.pages = [
            FakePage("Introduction to databases"),
            FakePage(None),
            FakePage("Database indexing"),
        ]


def test_extract_pages_preserves_page_numbers(monkeypatch):
    monkeypatch.setattr(pdf_service, "PdfReader", FakeReader)

    class FakePixmap:
        def tobytes(self, output_format):
            return b"fake image"

    class FakePdfPage:
        def get_pixmap(self, **kwargs):
            return FakePixmap()

    class FakePdf:
        def __getitem__(self, index):
            return FakePdfPage()

        def close(self):
            pass

    monkeypatch.setattr(
        pdf_service.pymupdf,
        "open",
        lambda file_path: FakePdf(),
    )

    # Page 2 has no selectable text, so simulate OCR returning no text.
    monkeypatch.setattr(
        pdf_service.pytesseract,
        "image_to_string",
        lambda image: "",
    )

    # Prevent PIL from trying to decode the fake image bytes.
    class FakeImage:
        pass

    monkeypatch.setattr(
        pdf_service.Image,
        "open",
        lambda image_bytes: FakeImage(),
    )

    pages = pdf_service.extract_pages("fake.pdf")

    assert pages == [
        {
            "page_number": 1,
            "text": "Introduction to databases",
        },
        {
            "page_number": 3,
            "text": "Database indexing",
        },
    ]


def test_chunk_text_splits_long_text():
    text = "A" * 25

    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert chunks == [
        "A" * 10,
        "A" * 10,
        "A" * 9,
    ]


def test_chunk_text_preserves_overlap():
    text = "abcdefghijklmnopqrst"

    chunks = chunk_text(text, chunk_size=10, overlap=3)

    assert chunks == [
        "abcdefghij",
        "hijklmnopq",
        "opqrst",
    ]


def test_chunk_text_returns_empty_list_for_blank_text():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_rejects_invalid_settings():
    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=0)

    with pytest.raises(ValueError):
        chunk_text("hello", overlap=-1)

    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=10, overlap=10)


def test_chunk_text_prefers_word_boundaries():
    text = "alpha beta gamma delta epsilon zeta eta theta"

    chunks = chunk_text(text, chunk_size=18, overlap=4)

    assert len(chunks) > 1

    for chunk in chunks[:-1]:
        assert chunk[-1] != " "


def test_chunk_pages_preserves_page_numbers():
    pages = [
        {
            "page_number": 1,
            "text": "A" * 25,
        },
        {
            "page_number": 3,
            "text": "B" * 12,
        },
    ]

    chunks = chunk_pages(
        pages,
        chunk_size=10,
        overlap=2,
    )

    assert [chunk["chunk_index"] for chunk in chunks] == [
        0, 1, 2, 3, 4
    ]

    assert [chunk["page_number"] for chunk in chunks] == [
        1, 1, 1, 3, 3
    ]

    assert all("content" in chunk for chunk in chunks)


def test_chunk_pages_handles_empty_pages():
    pages = [
        {"page_number": 1, "text": ""},
        {"page_number": 2, "text": "   "},
    ]

    assert chunk_pages(pages) == []
