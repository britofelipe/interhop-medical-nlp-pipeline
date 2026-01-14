from sqlalchemy.orm import Session
from src import models, schemas
import uuid
import datetime
from sqlalchemy import desc

# --- CREATE ---
def create_document(db: Session, filename: str, file_path: str):
    db_document = models.Document(
        filename=filename,
        file_path=file_path,
        status=models.ProcessingStatus.PENDING
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

# --- READ ---
def get_documents(db: Session, validated: bool = None, limit: int = 100):
    query = db.query(models.Document).outerjoin(models.Prescription)
    
    if validated is True:
        query = query.filter(models.Prescription.is_validated == True)
    elif validated is False:
        query = query.filter(
            (models.Prescription.is_validated == False) | 
            (models.Prescription.is_validated == None)
        )
        
    return query.order_by(desc(models.Document.upload_timestamp)).limit(limit).all()

def get_document(db: Session, document_id: uuid.UUID):
    return db.query(models.Document).filter(models.Document.id == document_id).first()

# --- UPDATE (Machine) ---
def update_prescription_structure(db: Session, document_id: uuid.UUID, data: dict):
    db_doc = get_document(db, document_id)
    if db_doc and db_doc.prescription:
        # Save to BOTH columns initially
        db_doc.prescription.structured_json = data 
        db_doc.prescription.ai_structured_json = data # <--- NEW: Save backup
        db.commit()
        return db_doc.prescription
    return None

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

# --- UPDATE (Human) ---
def validate_prescription(db: Session, document_id: uuid.UUID, validated_json: dict):
    """
    Saves the JSON corrected by the user and locks the document as Validated.
    """
    db_doc = get_document(db, document_id)
    if db_doc and db_doc.prescription:
        # Overwrite the machine data with human data
        db_doc.prescription.structured_json = validated_json
        db_doc.prescription.is_validated = True
        
        # Optionally, we could have a specific status for this
        # db_doc.status = models.ProcessingStatus.VALIDATED 
        
        db.commit()
        db.refresh(db_doc.prescription)
        return db_doc.prescription
    return None

def update_document_status(db: Session, document_id: uuid.UUID, status: str, error_message: str = None):
    db_doc = get_document(db, document_id)
    if db_doc:
        db_doc.status = status
        if error_message:
            print(f"Document {document_id} failed: {error_message}")
        db.commit()
        db.refresh(db_doc)
    return db_doc