from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from src.models import ProcessingStatus

# --- Document Schemas ---
class DocumentBase(BaseModel):
    filename: str

class DocumentCreate(DocumentBase):
    file_path: str

class DocumentResponse(DocumentBase):
    id: UUID
    status: ProcessingStatus
    upload_timestamp: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read SQLAlchemy models

# --- Prescription Schemas ---
class PrescriptionUpdate(BaseModel):
    structured_json: Dict[str, Any]
    is_validated: bool

class PrescriptionResponse(BaseModel):
    id: UUID
    document_id: UUID
    raw_text: Optional[str]
    structured_json: Optional[Dict[str, Any]]
    is_validated: bool

    class Config:
        from_attributes = True