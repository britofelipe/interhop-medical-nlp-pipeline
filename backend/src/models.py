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

# ... imports ...

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    raw_text = Column(Text, nullable=True)
    
    # NEW: Stores the original AI output (Read-Only for reference)
    ai_structured_json = Column(JSONB, nullable=True)
    
    # Stores the Current/Final version (Editable)
    structured_json = Column(JSONB, nullable=True)
    
    is_validated = Column(Boolean, default=False)

    document = relationship("Document", back_populates="prescription")
    