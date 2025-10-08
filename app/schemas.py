from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# Request/Response Schemas
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]
    providerMetadata: Optional[Dict[str, Any]] = None

class EmbeddingRequest(BaseModel):
    model: str
    input: str

class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[Dict[str, Any]]
    model: str
    usage: Dict[str, Any]
    providerMetadata: Optional[Dict[str, Any]] = None

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str

class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

class CreditsResponse(BaseModel):
    balance: str
    total_used: str
    usage_breakdown: Optional[Dict[str, str]] = None

# Database Schemas
class UserCreate(BaseModel):
    email: str
    api_key: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    organization_id: Optional[UUID]
    created_at: datetime

class RequestResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    provider: str
    model: str
    request_type: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    cost_usd: Optional[float]
    latency_ms: Optional[int]
    status: str
    created_at: datetime
