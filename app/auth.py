from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
import hashlib
import os

security = HTTPBearer()

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    salt = os.getenv("API_KEY_HASH_SALT", "default-salt")
    return hashlib.sha256(f"{api_key}{salt}".encode()).hexdigest()

def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify API key against hash"""
    return hash_api_key(api_key) == hashed_key

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from API key"""
    api_key = credentials.credentials
    
    # Find user by API key hash
    user = db.query(User).filter(
        User.api_key_hash == hash_api_key(api_key)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user

def create_user(email: str, api_key: str, db: Session) -> User:
    """Create a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create new user
    user = User(
        email=email,
        api_key_hash=hash_api_key(api_key)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user
