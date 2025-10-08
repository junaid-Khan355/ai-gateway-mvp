from sqlalchemy.orm import Session
from app.models import Request, ProviderCost
from app.schemas import ChatCompletionRequest, EmbeddingRequest
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

class CostTracker:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on provider pricing"""
        # Get pricing from database
        pricing = self.db.query(ProviderCost).filter(
            ProviderCost.provider == provider,
            ProviderCost.model == model
        ).first()
        
        if not pricing:
            # Default pricing if not found in database
            default_pricing = {
                "vercel": {"input": 0.001, "output": 0.002},
                "openai": {"input": 0.001, "output": 0.002},
                "anthropic": {"input": 0.003, "output": 0.015}
            }
            input_cost = default_pricing.get(provider, {}).get("input", 0.001)
            output_cost = default_pricing.get(provider, {}).get("output", 0.002)
        else:
            input_cost = float(pricing.input_cost_per_1k) / 1000
            output_cost = float(pricing.output_cost_per_1k) / 1000
        
        total_cost = (input_tokens * input_cost) + (output_tokens * output_cost)
        return round(total_cost, 6)
    
    def log_request(
        self,
        user_id: Optional[uuid.UUID],
        organization_id: Optional[uuid.UUID],
        provider: str,
        model: str,
        request_type: str,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        total_tokens: Optional[int],
        cost_usd: Optional[float],
        latency_ms: Optional[int],
        status: str,
        error_message: Optional[str] = None
    ) -> uuid.UUID:
        """Log a request to the database"""
        request = Request(
            user_id=user_id,
            organization_id=organization_id,
            provider=provider,
            model=model,
            request_type=request_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        return request.id
    
    def get_user_credits(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get user's credit balance and usage"""
        # Calculate total used
        total_used = self.db.query(Request).filter(
            Request.user_id == user_id,
            Request.status == "success"
        ).with_entities(Request.cost_usd).all()
        
        total_cost = sum(float(cost[0]) for cost in total_used if cost[0])
        
        # Calculate usage breakdown by provider
        provider_usage = self.db.query(
            Request.provider,
            Request.cost_usd
        ).filter(
            Request.user_id == user_id,
            Request.status == "success"
        ).all()
        
        usage_breakdown = {}
        for provider, cost in provider_usage:
            if cost:
                if provider not in usage_breakdown:
                    usage_breakdown[provider] = 0
                usage_breakdown[provider] += float(cost)
        
        # Convert to strings for API response
        usage_breakdown_str = {k: f"{v:.2f}" for k, v in usage_breakdown.items()}
        
        return {
            "balance": f"{100.00 - total_cost:.2f}",  # Assume $100 starting balance
            "total_used": f"{total_cost:.2f}",
            "usage_breakdown": usage_breakdown_str
        }
    
    def get_generation_details(self, generation_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get details for a specific generation"""
        request = self.db.query(Request).filter(Request.id == generation_id).first()
        
        if not request:
            return None
        
        return {
            "id": str(request.id),
            "total_cost": float(request.cost_usd) if request.cost_usd else 0,
            "usage": float(request.cost_usd) if request.cost_usd else 0,
            "created_at": request.created_at.isoformat(),
            "model": request.model,
            "provider_name": request.provider,
            "streamed": False,  # For now, assume non-streaming
            "latency": request.latency_ms or 0,
            "generation_time": request.latency_ms or 0,
            "tokens_prompt": request.input_tokens or 0,
            "tokens_completion": request.output_tokens or 0
        }
