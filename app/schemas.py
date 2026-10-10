from pydantic import BaseModel,ConfigDict
from datetime import datetime,UTC

class DocumentCreate(BaseModel):
    title : str
    subject : str

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id : int
    title : str
    subject : str
    created_at : datetime

class DocumentUpdate(BaseModel):
    title : str | None = None
    subject : str | None = None
