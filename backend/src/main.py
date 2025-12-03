import os
import shutil
import uuid
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import engine, get_db
from src import models, schemas, crud

# Create the database tables automatically on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="InterHop OCR API")

@app.get("/")
def read_root():
    return {"message": "InterHop Backend is running correctly"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Wrap the raw SQL string with text()
        db.execute(text("SELECT 1")) 
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
    
# UPLOAD
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload", response_model=schemas.DocumentResponse)
def upload_document(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """
    1. Validates file type.
    2. Saves file to disk.
    3. Creates DB record.
    """
    # 1. Validation: Ensure it's a PDF or Image
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only PDF, JPG, and PNG files are allowed.")

    # 2. Generate a unique filename to prevent overwriting
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 3. Save the file physically
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # 4. Create Database Record
    return crud.create_document(db=db, filename=file.filename, file_path=file_path)

@app.get("/documents/{document_id}", response_model=schemas.DocumentResponse)
def read_document(document_id: str, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, document_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_doc