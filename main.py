from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db, ImageJob
import uuid
import os
import shutil
from worker import process_image

# Initialize the API
app = FastAPI(title="Intelligent Media Processing Pipeline")

# Ensure the uploads directory exists on your computer
os.makedirs("uploads", exist_ok=True)

@app.get("/")
def root_check():
    return {"message": "Welcome to the gOGig Backend! The server is running."}

@app.post("/upload")
def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Generate a unique ID for this upload
    job_id = str(uuid.uuid4())
    
    # 2. Save the file locally to the /uploads folder
    file_extension = str(file.filename).split(".")[-1]
    file_path = f"uploads/{job_id}.{file_extension}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 3. Create a database record marked as "pending"
    new_job = ImageJob(id=job_id, file_path=file_path, status="pending")
    db.add(new_job)
    db.commit()
    
    # 4. Send the job to the Celery background worker
    process_image.delay(job_id)
    
    # 5. Return immediately to the user
    return {
        "job_id": job_id, 
        "status": "pending", 
        "message": "Image uploaded successfully and is in the queue."
    }

@app.get("/status/{job_id}")
def get_status(job_id: str, db: Session = Depends(get_db)):
    # Look up the job in the database
    job = db.query(ImageJob).filter(ImageJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "results": job.results,
        "error_reason": job.error_reason
    }