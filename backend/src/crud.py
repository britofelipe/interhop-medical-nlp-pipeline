from sqlalchemy.orm import Session
from src import models, schemas
import uuid
import datetime

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
def get_document(db: Session, document_id: uuid.UUID):
    return db.query(models.Document).filter(models.Document.id == document_id).first()

# --- UPDATE (Machine) ---
def update_document_text(db: Session, document_id: uuid.UUID, text: str):
    db_doc = get_document(db, document_id)
    if db_doc:
        if not db_doc.prescription:
            db_presc = models.Prescription(document_id=db_doc.id, raw_text=text, structured_json={})
            db.add(db_presc)
        else:
            db_doc.prescription.raw_text = text
        
        db_doc.status = models.ProcessingStatus.COMPLETED
        db.commit()
        db.refresh(db_doc)
    return db_doc

def update_prescription_structure(db: Session, document_id: uuid.UUID, data: dict):
    db_doc = get_document(db, document_id)
    if db_doc and db_doc.prescription:
        db_doc.prescription.structured_json = data 
        db.commit()
        return db_doc.prescription
    return None

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