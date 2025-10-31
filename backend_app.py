# ... (Full backend_app.py content from previous correct version) ...
import uvicorn; from fastapi import FastAPI, HTTPException; from fastapi.responses import FileResponse; from pantic import BaseModel; import logging; from celery.result import AsyncResult; from tasks import run_recommendation_pipeline, celery_app
app = FastAPI(title="Fertiler DSS API (Async)", description="API for asynchronous fertilizer recommendations.", version="0.4.0"); logging.basicConfig(level=logging.INFO); logger = logging.getLogger(__name__)
class RecommendationRequest(BaseModel): field_id: str; budget: float; crop: str
class JobResponse(BaseModel): job_id: str; status: str
@app.get("/", include_in_schema=False)
async def get_index_html(): return FileResponse("index.html")
@app.post("/recommend/request", response_model=JobResponse)
async def request_recommendation(request: RecommendationRequest): logger.info(f"Received job: field={request.field_id}, crop={request.crop}, budget={request.budget}"); if request.budget <= 0: raise HTTPException(status_code=400, detail="Budget must be positive."); try: job = run_recommendation_pipeline.delay(request.field_id, request.budget, request.crop); logger.info(f"Job dispatched: {job.id}"); return JobResponse(job_id=job.id, status="PENDING"); except Exception as e: logger.error(f"Dispatch error: {e}"); raise HTTPException(status_code=500, detail=str(e))
@app.get("/recommend/result/{job_id}")
async def get_job_result(job_id: str): logger.debug(f"Checking job: {job_id}"); job = AsyncResult(job_id, app=celery_app); if not job.ready(): return {"status": job.status, "data": None}; if job.failed(): logger.error(f"Job {job_id} failed: {job.result}"); return {"status": "FAILED", "data": str(job.result)}; if job.successful(): logger.info(f"Job {job_id} success."); return {"status": "SUCCESS", "data": job.get()}; return {"status": job.status, "data": None}
