import time
import logging
from celery import Celery
import os
from dotenv import load_dotenv
import pandas as pd

# --- This is the key integration step ---
# We import your *real* function from backend_skeleton.py
from backend_skeleton import featurize_field

# Load .env variables into the worker's environment
load_dotenv() 

# --- Celery Configuration ---
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

celery_app = Celery(
    'tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.run_recommendation_pipeline")
def run_recommendation_pipeline(field_id: str, budget: float, crop: str) -> dict:
    """
    This task now runs your REAL logic from backend_skeleton.py
    """
    logger.info(f"[JOB {celery_app.current_task.request.id}] Starting for field {field_id}, crop {crop}")

    try:
        # 1. Run your existing 'featurize_field' function
        logger.info(f"[JOB] Calling featurize_field for {field_id}...")
        X_df, X_dict = featurize_field(field_id, crop)
        logger.info(f"[JOB] Field features loaded: {X_dict}")

        # 2. Use your simulated recommendation
        # (This is from your backend_skeleton.py)
        rec_n = 120.0
        rec_p = 60.0
        rec_k = 40.0
        
        # 3. Simulate a plausible yield for the chart
        # We can base this on the *real* data we just fetched
        soil_n = X_dict.get('soil_n', 25.0) # Get real soil_n, default to 25
        # Simple mock yield model:
        optimized_yield = 120.0 + (soil_n * 0.2) + (budget / 50.0)
        
        # 4. Use our "smart risk" simulation from before
        base_uncertainty_pct = 0.10  # 10% base uncertainty
        n_risk_factor = (rec_n / 150.0) * 0.10 # More N = more risk
        
        total_std_dev = optimized_yield * (base_uncertainty_pct + n_risk_factor)
        ci_half_width = 1.96 * total_std_dev
        
        # 5. Format the final response for the UI
        response = {
            "field_id": field_id,
            "budget": budget,
            "crop": crop,
            "recommended_N": rec_n,
            "recommended_P": rec_p,
            "recommended_K": rec_k,
            "expected_yield_mean": optimized_yield,
            "expected_yield_95_ci_low": optimized_yield - ci_half_width,
            "expected_yield_95_ci_high": optimized_yield + ci_half_width,
            "weather_summary": {
                "total_rainfall_mm": X_dict.get("total_rainfall"),
                "gdd": X_dict.get("gdd"),
                "mean_temp": X_dict.get("mean_temp")
            },
            "message": "Recommendation successful."
        }
        
        logger.info(f"[JOB {celery_app.current_task.request.id}] Completed successfully.")
        return response

    except Exception as e:
        logger.error(f"[JOB {celery_app.current_task.request.id}] FAILED: {e}")
        # Log the full traceback
        import traceback
        logger.error(traceback.format_exc())
        raise e
