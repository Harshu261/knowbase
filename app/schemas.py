from pydantic import BaseModel
from datetime import datetime

class DocumentCreate(BaseModel):
    title : str
    subject : str

class DocumentResponse(BaseModel):
    id : int
    title : str
    subject : str
    created_at : datetime

    class Config :
        from_attributes  = True
class DocumentUpdate(BaseModel):
    title : str | None = None
    subject : str | None = None
