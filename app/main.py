from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import Base
from app.schemas import (
    ChatCompletionRequest, ChatCompletionResponse,
    EmbeddingRequest, EmbeddingResponse,
    ModelsResponse, CreditsResponse,
    UserCreate, UserResponse
)
from app.router import ProviderRouter
from app.cost_tracker import CostTracker
from app.auth import get_current_user, create_user
from app.models import User
import uuid
import time

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Gateway",
    description="OpenAI-compatible AI Gateway with cost tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize router
router = ProviderRouter()

@app.get("/")
async def root():
    return {"message": "AI Gateway is running!"}

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """OpenAI-compatible chat completions endpoint"""
    cost_tracker = CostTracker(db)
    
    try:
        # Route request to appropriate provider
        result = await router.chat_completion(request)
        
        # Extract usage information
        usage = result.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        # Calculate cost
        provider = result.get("providerMetadata", {}).get("gateway", {}).get("provider", "unknown")
        cost = cost_tracker.calculate_cost(provider, request.model, input_tokens, output_tokens)
        
        # Log request
        request_id = cost_tracker.log_request(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            provider=provider,
            model=request.model,
            request_type="chat",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=result.get("providerMetadata", {}).get("gateway", {}).get("latency"),
            status="success"
        )
        
        # Add generation ID to response
        result["id"] = f"gen_{request_id.hex}"
        
        return result
        
    except Exception as e:
        # Log failed request
        cost_tracker.log_request(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            provider="unknown",
            model=request.model,
            request_type="chat",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0,
            latency_ms=0,
            status="error",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request failed: {str(e)}"
        )

@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def embeddings(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """OpenAI-compatible embeddings endpoint"""
    cost_tracker = CostTracker(db)
    
    try:
        # Route request to appropriate provider
        result = await router.embedding(request)
        
        # Extract usage information
        usage = result.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        # Calculate cost
        provider = result.get("providerMetadata", {}).get("gateway", {}).get("provider", "unknown")
        cost = cost_tracker.calculate_cost(provider, request.model, input_tokens, 0)
        
        # Log request
        request_id = cost_tracker.log_request(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            provider=provider,
            model=request.model,
            request_type="embedding",
            input_tokens=input_tokens,
            output_tokens=0,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=result.get("providerMetadata", {}).get("gateway", {}).get("latency"),
            status="success"
        )
        
        return result
        
    except Exception as e:
        # Log failed request
        cost_tracker.log_request(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            provider="unknown",
            model=request.model,
            request_type="embedding",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0,
            latency_ms=0,
            status="error",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request failed: {str(e)}"
        )

@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """List available models from all providers"""
    try:
        result = await router.get_models()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch models: {str(e)}"
        )

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """Get specific model information"""
    try:
        models = await router.get_models()
        for model in models["data"]:
            if model["id"] == model_id:
                return model
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch model: {str(e)}"
        )

@app.get("/v1/credits", response_model=CreditsResponse)
async def get_credits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's credit balance and usage"""
    cost_tracker = CostTracker(db)
    credits = cost_tracker.get_user_credits(current_user.id)
    return credits

@app.get("/v1/generation")
async def get_generation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get generation details by ID"""
    try:
        # Convert string ID to UUID
        generation_id = uuid.UUID(id.replace("gen_", ""))
        
        cost_tracker = CostTracker(db)
        generation = cost_tracker.get_generation_details(generation_id)
        
        if not generation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation not found"
            )
        
        return {"data": generation}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid generation ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch generation: {str(e)}"
        )

@app.post("/v1/users", response_model=UserResponse)
async def create_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user (for testing purposes)"""
    try:
        user = create_user(user_data.email, user_data.api_key, db)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
