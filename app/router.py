from app.providers import VercelProvider
from app.schemas import ChatCompletionRequest, EmbeddingRequest
from typing import Dict, Any
import random

class ProviderRouter:
    def __init__(self):
        self.providers = {
            "vercel": VercelProvider()
        }
        
        # Only use Vercel for all models
        self.routing_preferences = {
            "anthropic/claude": ["vercel"],
            "openai/gpt": ["vercel"],
            "anthropic/claude-sonnet": ["vercel"],
            "anthropic/claude-haiku": ["vercel"],
            "openai/gpt-4": ["vercel"],
            "openai/gpt-3.5": ["vercel"]
        }
    
    def select_provider(self, model: str) -> str:
        """Always select Vercel"""
        return "vercel"
    
    async def chat_completion(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """Route chat completion request to Vercel"""
        provider = self.providers["vercel"]
        
        try:
            result = await provider.chat_completion(request)
            return result
        except Exception as e:
            raise e
    
    async def embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        """Route embedding request to Vercel"""
        provider = self.providers["vercel"]
        
        try:
            result = await provider.embedding(request)
            return result
        except Exception as e:
            raise e
    
    async def get_models(self) -> Dict[str, Any]:
        """Get models from Vercel"""
        try:
            provider = self.providers["vercel"]
            models_response = await provider.get_models()
            return models_response
        except Exception as e:
            raise e
    
    def get_provider(self, provider_name: str):
        """Get a specific provider instance"""
        return self.providers.get(provider_name)
