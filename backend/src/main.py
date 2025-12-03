import os
import shutil
import uuid
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import engine, get_db
from src import models, schemas, crud
from fastapi import BackgroundTasks
from src.modules.generator.service import PrescriptionGenerator

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

# SYNTHETIC PRESCRIPTION GENERATION

# Define where synthetic data lives
SYNTHETIC_DIR = "/app/uploads/synthetic"

@app.post("/admin/generate-synthetic-data")
def generate_synthetic_data(
    count: int = 5, 
    background_tasks: BackgroundTasks = None
):
    """
    Triggers the generation of synthetic prescriptions.
    """
    generator = PrescriptionGenerator(output_dir=SYNTHETIC_DIR)
    
    # Run generation in background so API doesn't freeze
    background_tasks.add_task(generator.generate_batch, count=count)
    
    return {
        "message": f"Started generating {count} synthetic documents.",
        "output_directory": SYNTHETIC_DIR
    }

@app.get("/admin/synthetic-files")
def list_synthetic_files():
    """List generated files for verification"""
    if not os.path.exists(SYNTHETIC_DIR):
        return []
    return os.listdir(SYNTHETIC_DIR)

@app.post("/admin/upload-mimic-csv")
def upload_mimic_csv(file: UploadFile = File(...)):
    """
    Upload the MIMIC Prescriptions CSV to be used for generation.
    """
    file_location = os.path.join(UPLOAD_DIR, "mimic_prescriptions.csv")
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"message": "CSV uploaded successfully", "path": file_location}

@app.post("/admin/generate-synthetic-data")
def generate_synthetic_data(
    count: int = 5, 
    background_tasks: BackgroundTasks = None
):
    # Check if the MIMIC CSV exists, otherwise use Mock data
    csv_path = os.path.join(UPLOAD_DIR, "mimic_prescriptions.csv")
    if not os.path.exists(csv_path):
        csv_path = None # Triggers mock data fallback
        
    generator = PrescriptionGenerator(output_dir=SYNTHETIC_DIR)
    background_tasks.add_task(generator.generate_batch, count=count, csv_path=csv_path)
    
    return {
        "message": f"Generating {count} documents...",
        "source": "MIMIC CSV" if csv_path else "Internal Mock Data",
        "output_directory": SYNTHETIC_DIR
    }