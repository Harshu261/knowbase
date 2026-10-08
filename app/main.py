from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

@app.get('/')
def root():
    return {"message" : "Welcome to Knowbase"}
@app.get('/health')
def health_check():
    return{"status" : "ok"}

class DocumentCreate(BaseModel):
    title : str
    subject : str
class DocumentResponse(BaseModel):
    title : str
    subject : str
@app.post("/documents",
          status_code=201,
          response_model=DocumentResponse)
def create_document(document : DocumentCreate):
    return {
        "message" : "Document Created",
        "document" : document
    }
