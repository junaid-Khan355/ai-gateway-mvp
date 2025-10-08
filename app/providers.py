import httpx
import os
import time
from typing import Dict, Any, Optional
from app.schemas import ChatCompletionRequest, EmbeddingRequest

class BaseProvider:
    def __init__(self, name: str, base_url: str, api_key: str):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def chat_completion(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def get_models(self) -> Dict[str, Any]:
        raise NotImplementedError

class VercelProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            name="vercel",
            base_url="https://ai-gateway.vercel.sh/v1",
            api_key=os.getenv("VERCEL_AI_GATEWAY_API_KEY", "")
        )
    
    async def chat_completion(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "stream": request.stream,
            "temperature": request.temperature,
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        start_time = time.time()
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        response.raise_for_status()
        result = response.json()
        
        # Add provider metadata
        result["providerMetadata"] = {
            "gateway": {
                "provider": self.name,
                "latency": latency_ms,
                "routing": {
                    "selected_provider": self.name
                }
            }
        }
        
        return result
    
    async def embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model,
            "input": request.input
        }
        
        start_time = time.time()
        response = await self.client.post(
            f"{self.base_url}/embeddings",
            headers=headers,
            json=payload
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        response.raise_for_status()
        result = response.json()
        
        # Add provider metadata
        result["providerMetadata"] = {
            "gateway": {
                "provider": self.name,
                "latency": latency_ms
            }
        }
        
        return result
    
    async def get_models(self) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = await self.client.get(f"{self.base_url}/models", headers=headers)
        response.raise_for_status()
        return response.json()

class OpenAIProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            name="openai",
            base_url="https://api.openai.com/v1",
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
    
    async def chat_completion(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model.replace("openai/", ""),  # Remove prefix
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "stream": request.stream,
            "temperature": request.temperature,
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        start_time = time.time()
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        response.raise_for_status()
        result = response.json()
        
        # Add provider metadata
        result["providerMetadata"] = {
            "gateway": {
                "provider": self.name,
                "latency": latency_ms,
                "routing": {
                    "selected_provider": self.name
                }
            }
        }
        
        return result
    
    async def embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model.replace("openai/", ""),  # Remove prefix
            "input": request.input
        }
        
        start_time = time.time()
        response = await self.client.post(
            f"{self.base_url}/embeddings",
            headers=headers,
            json=payload
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        response.raise_for_status()
        result = response.json()
        
        # Add provider metadata
        result["providerMetadata"] = {
            "gateway": {
                "provider": self.name,
                "latency": latency_ms
            }
        }
        
        return result
    
    async def get_models(self) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = await self.client.get(f"{self.base_url}/models", headers=headers)
        response.raise_for_status()
        return response.json()

class AnthropicProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            name="anthropic",
            base_url="https://api.anthropic.com/v1",
            api_key=os.getenv("ANTHROPIC_API_KEY", "")
        )
    
    async def chat_completion(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert OpenAI format to Anthropic format
        model = request.model.replace("anthropic/", "")
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1000,
            "temperature": request.temperature,
        }
        
        start_time = time.time()
        response = await self.client.post(
            f"{self.base_url}/messages",
            headers=headers,
            json=payload
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        response.raise_for_status()
        result = response.json()
        
        # Convert Anthropic response to OpenAI format
        openai_response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["content"][0]["text"]
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": result["usage"]["input_tokens"],
                "completion_tokens": result["usage"]["output_tokens"],
                "total_tokens": result["usage"]["input_tokens"] + result["usage"]["output_tokens"]
            },
            "providerMetadata": {
                "gateway": {
                    "provider": self.name,
                    "latency": latency_ms,
                    "routing": {
                        "selected_provider": self.name
                    }
                }
            }
        }
        
        return openai_response
    
    async def embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        # Anthropic doesn't have embeddings, return error
        raise NotImplementedError("Anthropic doesn't support embeddings")
    
    async def get_models(self) -> Dict[str, Any]:
        # Return Anthropic models in OpenAI format
        return {
            "object": "list",
            "data": [
                {
                    "id": "anthropic/claude-3-sonnet-20240229",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "anthropic"
                },
                {
                    "id": "anthropic/claude-3-haiku-20240307",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "anthropic"
                }
            ]
        }
