from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src import models
from src.modules.evaluation.service import MetricsService

router = APIRouter(prefix="/statistics", tags=["statistics"])
metrics_service = MetricsService()

@router.get("/global")
def get_global_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated performance metrics based on human validation.
    """
    # Fetch all VALIDATED prescriptions
    prescriptions = db.query(models.Prescription).filter(
        models.Prescription.is_validated == True
    ).all()

    return metrics_service.aggregate_stats(prescriptions)