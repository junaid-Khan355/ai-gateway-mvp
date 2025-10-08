from sqlalchemy import create_engine
from app.models import Base
import os
from dotenv import load_dotenv
import sys

load_dotenv()

def setup_database():
    """Create database tables"""
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_gateway")
    
    try:
        engine = create_engine(database_url)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("Database tables created successfully!")
        return True
    except Exception as e:
        print(f"Database setup failed: {e}")
        print("This is expected during build phase. Database will be set up at runtime.")
        return False

if __name__ == "__main__":
    success = setup_database()
    if not success:
        sys.exit(0)  # Exit gracefully during build
