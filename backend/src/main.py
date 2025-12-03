from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import engine, get_db
from src import models

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