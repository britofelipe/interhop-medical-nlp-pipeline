# interhop-medical-nlp-pipeline

**Open-source pipeline for structuring unstructured medical documents (PDFs, images of prescriptions) using Computer Vision and Natural Language Processing (NLP).**

This project aims to automate the recognition and normalization of medical prescriptions to assist healthcare professionals by reducing administrative overhead and improving care continuity.

## 🏗 Architecture

The project is built as a modular microservices architecture using Docker:

* **Frontend:** Python (Streamlit) - User interface for uploading and validating documents.
* **Backend:** Python (FastAPI) - API handling OCR logic, entity extraction, and database communication.
* **Database:** PostgreSQL - Stores document metadata and structured results.

## 🚀 Getting Started

### Prerequisites
* Docker & Docker Compose

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd interhop-medical-nlp-pipeline
    ```

2.  **Configure Environment:**
    Create a `.env` file in the root directory with the corresponding information

3.  **Run with Docker:**
    Build and start the services:
    ```bash
    docker-compose up --build
    ```
    or
    ```bash
    docker compose up --build
    ```

    depending on your Docker version

### Accessing the Services

Once the containers are running:

* **Frontend (Streamlit):** [http://localhost:8501](http://localhost:8501)
* **Backend API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Database:** Port `5432` (accessible via external tools like DBeaver).
