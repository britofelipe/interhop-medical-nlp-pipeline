import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

# Enum for the status of the document processing
class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"

    # UUID is better than Integer ID for distributed systems/security
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False) # Internal path in Docker volume
    
    # Enum column
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    
    # Auto-generated timestamp
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to the extraction result
    prescription = relationship("Prescription", back_populates="document", uselist=False)

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Key linking to the Document
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Full raw text extracted by OCR (Tesseract)
    raw_text = Column(Text, nullable=True)
    
    # Structured data (Drugs, Dosages, etc.)
    # JSONB is binary JSON - allows for high-performance querying inside the JSON
    structured_json = Column(JSONB, nullable=True)
    
    # Has a human doctor validated this?
    is_validated = Column(Boolean, default=False)

    # Back relationship
    document = relationship("Document", back_populates="prescription")