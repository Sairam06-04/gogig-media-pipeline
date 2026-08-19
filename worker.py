import os
from dotenv import load_dotenv
from celery import Celery
from database import SessionLocal, ImageJob
from services import analyze_image  # Importing our new analysis engine

# Load environment variables
load_dotenv()

# Cloud-Ready: Uses Render's REDIS_URL if available, otherwise falls back to local Docker Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Configure Celery to use the Redis broker
celery_app = Celery(
    "image_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

@celery_app.task
def process_image(job_id: str):
    # 1. Open a database session
    db = SessionLocal()
    job = db.query(ImageJob).filter(ImageJob.id == job_id).first()
    
    if not job:
        db.close()
        return
    
    # 2. Update status to "processing"
    job.status = "processing" # type: ignore
    db.commit()
    
    try:
        print(f"Starting actual analysis for job: {job_id}")
        
        # 3. Run our 4 real analysis checks using the file path saved in the DB
        analysis_results = analyze_image(job.file_path)
        
        # 4. Save the real results and mark as completed
        job.results = analysis_results # type: ignore
        job.status = "completed" # type: ignore
        db.commit()
        
    except Exception as e:
        # 5. If anything crashes, mark as failed so we can debug it
        job.status = "failed" # type: ignore
        job.error_reason = str(e) # type: ignore
        db.commit()
    finally:
        db.close()