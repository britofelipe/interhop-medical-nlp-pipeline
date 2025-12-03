import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from src.modules.generator.service import PrescriptionGenerator
from src.benchmark import BenchmarkRunner

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

UPLOAD_DIR = "/app/uploads"
SYNTHETIC_DIR = "/app/uploads/synthetic"

@router.post("/generate-synthetic-data")
def generate_synthetic_data(count: int = 5, background_tasks: BackgroundTasks = None):
    csv_path = os.path.join(UPLOAD_DIR, "mimic_prescriptions.csv")
    if not os.path.exists(csv_path):
        csv_path = None
        
    generator = PrescriptionGenerator(output_dir=SYNTHETIC_DIR)
    background_tasks.add_task(generator.generate_batch, count=count, csv_path=csv_path)
    
    return {"message": f"Generating {count} documents..."}

@router.post("/run-benchmark")
def run_benchmark_test():
    runner = BenchmarkRunner()
    return runner.run_full_benchmark()
