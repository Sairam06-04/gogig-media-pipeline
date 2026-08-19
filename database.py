import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Cloud-Ready: Uses Render's DATABASE_URL if available, otherwise falls back to local Docker DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@localhost:5432/gogig_db")

# Set up the connection engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# This is the blueprint for our database table
class ImageJob(Base):
    __tablename__ = "image_jobs"
    
    # We are storing the unique ID, where the file is saved, the current status, and the final results
    id = Column(String, primary_key=True, index=True)
    file_path = Column(String)
    status = Column(String, default="pending")  # pending, processing, completed, or failed
    results = Column(JSON, nullable=True)
    error_reason = Column(String, nullable=True)

# This command automatically creates the table in Postgres for us
Base.metadata.create_all(bind=engine)

# A simple helper function to open and close database connections safely
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()