from sqlalchemy import create_engine
from app.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    """Create database tables"""
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_gateway")
    
    engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")

if __name__ == "__main__":
    setup_database()
