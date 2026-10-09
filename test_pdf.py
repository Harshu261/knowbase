from pypdf import PdfReader

file_path = "uploads/e3cabb0e-0fb4-46dc-baf1-68aa28853c9e.pdf"

reader = PdfReader(file_path)

print("PDF opened successfully")
print("Number of pages:", len(reader.pages))

for index, page in enumerate(reader.pages):
    print(f"Testing page {index + 1}")

    try:
        text = page.extract_text()
        print("Extracted characters:", len(text or ""))
        print(repr((text or "")[:200]))
    except Exception as error:
        print("Page extraction failed:", repr(error))
