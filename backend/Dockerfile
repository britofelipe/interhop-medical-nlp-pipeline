FROM python:3.10-slim

# Install system dependencies for OCR and Image Processing
# tesseract-ocr: The OCR engine
# poppler-utils: Required for pdf2image to convert PDFs to images
# libgl1...: Required for OpenCV
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-fra \
    poppler-utils \
    libgl1 \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run FastAPI with hot-reloading enabled
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]