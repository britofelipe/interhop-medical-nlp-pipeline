import os
from fastapi import FastAPI
from src.database import engine
from src import models
from src.routers import documents, admin, statistics

# 1. Create Database Tables
models.Base.metadata.create_all(bind=engine)

# 2. Initialize App
app = FastAPI(
    title="InterHop OCR API",
    description="API for extracting and structuring medical prescriptions.",
    version="1.0.0"
)

# 3. Ensure Storage Exists
os.makedirs("/app/uploads", exist_ok=True)
os.makedirs("/app/uploads/synthetic", exist_ok=True)

# 4. Include Routers
app.include_router(documents.router)
app.include_router(admin.router)
app.include_router(statistics.router)

@app.get("/")
def read_root():
    return {"message": "InterHop Backend is running", "docs_url": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok"}