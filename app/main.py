from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
import os
import json
import asyncio

app = FastAPI(
    title="AI Gateway",
    description="OpenAI-compatible AI Gateway with cost tracking",
    version="1.0.0"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    if request.url.path.startswith("/v1/"):
        body = await request.body()
        print(f"\n🔍 Incoming Request to {request.url.path}")
        print(f"   Method: {request.method}")
        print(f"   Headers: {dict(request.headers)}")
        if body:
            try:
                body_json = json.loads(body)
                print(f"   Body: {json.dumps(body_json, indent=2)}")
            except:
                print(f"   Body (raw): {body.decode()}")
        
        # Important: Re-create request with body for downstream processing
        async def receive():
            return {"type": "http.request", "body": body}
        
        request._receive = receive
    
    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully!")
        print("✅ AI Gateway startup completed!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("⚠️ Continuing startup without database...")
        # Don't fail startup, let the app run and handle DB errors gracefully

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

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "message": "AI Gateway is running!"}

@app.get("/debug-streaming")
async def debug_streaming():
    """Debug endpoint to test streaming logic"""
    return {
        "streaming_support": True,
        "message": "Streaming endpoint is accessible",
        "timestamp": time.time()
    }

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """OpenAI-compatible chat completions endpoint"""
    # Debug logging
    print(f"📝 Received chat completion request:")
    print(f"   Model: {request.model}")
    print(f"   Messages: {len(request.messages)} message(s)")
    print(f"   Temperature: {request.temperature}")
    print(f"   Max tokens: {request.max_tokens}")
    print(f"   Stream: {request.stream}")
    
    cost_tracker = CostTracker(db)
    
    # Handle streaming response first
    if request.stream:
        print("🌊 Processing streaming response")
        print(f"🔍 Request stream flag: {request.stream}")
        from fastapi.responses import StreamingResponse
        import json
        import asyncio
        
        # Convert streaming request to non-streaming for provider
        print("⚠️ Converting streaming request to non-streaming for compatibility")
        request.stream = False
        
        # Get non-streaming response first
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
            request_type="chat_stream",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=result.get("providerMetadata", {}).get("gateway", {}).get("latency"),
            status="success"
        )
        
        # Get the response content
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Create streaming response
        async def generate_stream():
            # Send initial chunk
            initial_chunk = {
                "id": f"gen_{request_id.hex}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"
            
            # Split content into words for streaming effect
            words = content.split()
            for i, word in enumerate(words):
                chunk = {
                    "id": f"gen_{request_id.hex}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": word + (" " if i < len(words) - 1 else "")},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send final chunk
            final_chunk = {
                "id": f"gen_{request_id.hex}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    
    # Non-streaming response (existing logic)
    try:
        # Route request to appropriate provider
        result = await router.chat_completion(request)
        print(f"🔍 Provider result type: {type(result)}")
        print(f"🔍 Provider result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
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
        print(f"❌ Error processing request: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Log failed request
        try:
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
        except Exception as log_error:
            print(f"⚠️ Failed to log error: {log_error}")
        
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
