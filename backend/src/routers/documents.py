import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from src.database import get_db, SessionLocal
from src import models, schemas, crud
from src.modules.vision.service import OCRService
from src.modules.extraction.service import ExtractionService

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

# Services
ocr_service = OCRService()
extraction_service = ExtractionService()
UPLOAD_DIR = "/app/uploads"

# --- BACKGROUND TASK LOGIC ---
def process_document_task(doc_id: uuid.UUID, file_path: str):
    """
    1. OCR (Vision)
    2. Extraction (NLP)
    3. Save to DB
    """
    db = SessionLocal()
    try:
        # 1. OCR
        print(f"Starting OCR for {doc_id}")
        raw_text = ocr_service.process_file(file_path)
        crud.update_document_text(db, doc_id, raw_text)

        # 2. Extraction
        print(f"Starting Extraction for {doc_id}")
        structured_data = extraction_service.extract_from_text(raw_text)
        crud.update_prescription_structure(db, doc_id, structured_data)

        print(f"Processing complete for {doc_id}")
    except Exception as e:
        print(f"Error processing {doc_id}: {e}")
        # Ideally set status to FAILED here
    finally:
        db.close()

# --- ENDPOINTS ---

@router.post("/upload", response_model=schemas.DocumentResponse)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """
    Phase 4 Goal: Saves file, creates DB entry, triggers OCR.
    """
    # 1. Validation
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # 2. Save File
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Create DB Entry
    doc = crud.create_document(db=db, filename=file.filename, file_path=file_path)

    # 4. Trigger Background Task Immediately
    background_tasks.add_task(process_document_task, doc.id, file_path)

    return doc

@router.get("/{document_id}/status", response_model=schemas.DocumentResponse)
def get_document_status(document_id: str, db: Session = Depends(get_db)):
    """
    Check if OCR is done.
    """
    db_doc = crud.get_document(db, document_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_doc

@router.get("/{document_id}/result", response_model=schemas.PrescriptionResponse)
def get_document_result(document_id: str, db: Session = Depends(get_db)):
    """
    Returns the JSON structured data.
    """
    db_doc = crud.get_document(db, document_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not db_doc.prescription:
        raise HTTPException(status_code=404, detail="Results not ready yet")
        
    return db_doc.prescription

@router.put("/{document_id}/validate", response_model=schemas.PrescriptionResponse)
def validate_document(
    document_id: str, 
    validation_data: schemas.PrescriptionUpdate, # We need to ensure this Schema exists
    db: Session = Depends(get_db)
):
    """
    Accepts corrected JSON from User and marks as Validated.
    """
    db_doc = crud.get_document(db, document_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    updated_prescription = crud.validate_prescription(
        db, 
        document_id, 
        validation_data.structured_json
    )
    return updated_prescription
