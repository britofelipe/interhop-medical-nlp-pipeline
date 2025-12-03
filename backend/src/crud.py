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
