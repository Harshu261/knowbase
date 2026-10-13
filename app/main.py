from pathlib import Path
from uuid import uuid4
import shutil

from app.pdf_service import extract_text, extract_pages, chunk_pages

from fastapi import UploadFile,File,Form

from fastapi import FastAPI, Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Session

from fastapi import Query

from app.database import get_db
from app.models import Document,DocumentChunk
from app.schemas import DocumentCreate,DocumentResponse,DocumentUpdate
from app.pdf_service import extract_text

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)


@app.get("/")
def root():
    return {"message": "Welcome to KnowBase"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/documents",
          response_model=DocumentResponse,
             status_code=201)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    new_document = Document(
        title=document.title,
        subject=document.subject
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document
@app.get("/documents",
         response_model=list[DocumentResponse])
def get_documents(db:Session = Depends(get_db)):
    documents = db.query(Document).all()

    return documents


@app.get(
    "/documents/search",
    response_model=list[DocumentResponse]
)
def search_documents(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    if not q.strip():
        raise HTTPException(
            status_code=422,
            detail="Search query cannot be empty or whitespace."
    )
    search_query = func.plainto_tsquery("english", q)

    document_vector = func.to_tsvector(
        "english",
        func.coalesce(Document.content, "")
    )

    relevance = func.ts_rank(
        document_vector,
        search_query
    )

    documents = (
        db.query(Document)
        .filter(document_vector.op("@@")(search_query))
        .order_by(relevance.desc())
        .all()
    )

    return documents

@app.get("/documents/{document_id}",
         response_model=DocumentResponse)
def get_document(
    document_id:int,
    db:Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
    ).first()

    if document is None:
        raise HTTPException(
        status_code=404,
        detail="Document not found"
        )
    return document

@app.delete("/document/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    file_path = document.file_path

    try:
        # SQLAlchemy relationship cascade deletes the associated chunks.
        db.delete(document)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Delete the PDF only after the database commit succeeds.
    if file_path:
        path = Path(file_path)

        try:
            # Only remove files stored inside KnowBase's uploads directory.
            if path.resolve().parent == UPLOAD_DIR.resolve():
                path.unlink(missing_ok=True)
        except OSError:
            # The database deletion has already succeeded.
            # A file cleanup failure should not undo that deletion.
            pass

@app.patch("/documents/{document_id}",response_model=DocumentResponse)
def update_document(
    document_id : int,
    updates : DocumentUpdate,
    db : Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()
    if document is None :
        raise HTTPException(
            status_code = 404,
            detail = "Document not found"
        )
    update_data = updates.model_dump(exclude_unset=True)

    for field,value in update_data.items():
        if value is None :
            raise HTTPException(
                status_code = 422,
                detail = f"{field} cannot be NULL"
            )
        setattr(document,field,value)
    db.commit()
    db.refresh(document)
    return document


@app.post("/documents/upload", status_code=201)
def upload_document(
    title: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=415,
            detail="Only PDF files are allowed",
        )

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=415,
            detail="The file must end with .pdf",
        )

    stored_filename = f"{uuid4()}.pdf"
    file_path = UPLOAD_DIR / stored_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)


        pages = extract_pages(str(file_path))
        extracted_content = "\n\n".join(
            page["text"] for page in pages
        ).strip()

        if not extracted_content:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text could be extracted from this PDF. "
                    "The file may be blank, damaged, or unreadable by OCR."
                ),
            )


        new_document = Document(
            title=title,
            subject=subject,
            file_path=str(file_path),
            content=extracted_content,
        )

        db.add(new_document)
        db.flush()

        chunks = chunk_pages(pages)

        chunk_records = [
            DocumentChunk(
                document_id=new_document.id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"],
                content=chunk["content"],
            )
            for chunk in chunks
        ]

        db.add_all(chunk_records)
        db.commit()
        db.refresh(new_document)

    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    finally:
        file.file.close()

    return {
        "message": "pdf uploaded successfully",
        "document": new_document,
        "stored_filename": stored_filename,
        "chunks_created": len(chunks),
    }
