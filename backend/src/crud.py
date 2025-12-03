from sqlalchemy.orm import Session
from src import models, schemas
import uuid

def create_document(db: Session, filename: str, file_path: str):
    """
    Creates a new document record in the database with status 'pending'.
    """
    db_document = models.Document(
        filename=filename,
        file_path=file_path,
        status=models.ProcessingStatus.PENDING
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_document(db: Session, document_id: uuid.UUID):
    return db.query(models.Document).filter(models.Document.id == document_id).first()

# TESSERACT OCR PROCESSING RECORDS

def update_document_text(db: Session, document_id: uuid.UUID, text: str):
    """Updates the document with OCR results and marks it as COMPLETED."""
    db_doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_doc:
        # Create or update the associated Prescription record
        if not db_doc.prescription:
            db_presc = models.Prescription(
                document_id=db_doc.id, 
                raw_text=text, 
                structured_json={}
            )
            db.add(db_presc)
        else:
            db_doc.prescription.raw_text = text
        
        db_doc.status = models.ProcessingStatus.COMPLETED
        db.commit()
        db.refresh(db_doc)
    return db_doc
