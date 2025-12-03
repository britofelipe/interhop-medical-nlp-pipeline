from fastapi import FastAPI

app = FastAPI(title="InterHop OCR API")

@app.get("/")
def read_root():
    return {"message": "InterHop Backend is running correctly"}

@app.get("/health")
def health_check():
    return {"status": "ok"}