from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Ollama Configuration (Local Mode)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    
    # OpenRouter Configuration (General Mode)
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"  # Default to fast model
    
    # Available OpenRouter Models (Fast + Flagship)
    available_models: list = [
        # FAST MODELS (optimized for speed)
        {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini (Fast)", "provider": "openai", "category": "fast"},
        {"id": "anthropic/claude-3-5-haiku", "name": "Claude 3.5 Haiku (Fast)", "provider": "anthropic", "category": "fast"},
        {"id": "google/gemini-flash-1.5", "name": "Gemini 1.5 Flash (Fast)", "provider": "google", "category": "fast"},
        {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat (Fast)", "provider": "deepseek", "category": "fast"},
        {"id": "x-ai/grok-beta", "name": "Grok Beta (Fast)", "provider": "x-ai", "category": "fast"},
        {"id": "mistralai/mistral-small-latest", "name": "Mistral Small (Fast)", "provider": "mistralai", "category": "fast"},
        
        # FLAGSHIP MODELS (most capable)
        {"id": "anthropic/claude-opus-4-20250514", "name": "Claude Opus 4 (Flagship)", "provider": "anthropic", "category": "flagship"},
        {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo (Flagship)", "provider": "openai", "category": "flagship"},
        {"id": "google/gemini-pro-1.5-exp", "name": "Gemini Pro 1.5 Exp (Flagship)", "provider": "google", "category": "flagship"},
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet (Flagship)", "provider": "anthropic", "category": "flagship"},
        {"id": "openai/gpt-4o", "name": "GPT-4o (Flagship)", "provider": "openai", "category": "flagship"},
        {"id": "x-ai/grok-2-1212", "name": "Grok 2 (Flagship)", "provider": "x-ai", "category": "flagship"},
        {"id": "deepseek/deepseek-chat-v3", "name": "DeepSeek V3 (Flagship)", "provider": "deepseek", "category": "flagship"},
        {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B (Flagship)", "provider": "meta-llama", "category": "flagship"},
        
        # BALANCED
        {"id": "anthropic/claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (Balanced)", "provider": "anthropic", "category": "balanced"},
    ]
    
    # Available Ollama Models
    available_ollama_models: list = [
        {"id": "llama3", "name": "Llama 3", "size": "8B"},
        {"id": "hf.co/Yusiko/LIA", "name": "LIA (Llama 3.1 Finetuned)", "size": "custom"},
        {"id": "gemma3:12b", "name": "Gemma 3 12B", "size": "12B"},
        {"id": "mistral", "name": "Mistral 7B", "size": "7B"},
        {"id": "codellama", "name": "Code Llama", "size": "7B"},
        {"id": "phi3", "name": "Phi-3", "size": "3.8B"},
        {"id": "qwen", "name": "Qwen", "size": "7B"},
        {"id": "neural-chat", "name": "Neural Chat", "size": "7B"},
        {"id": "starling-lm", "name": "Starling LM", "size": "7B"}
    ]
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    allowed_directories: str = os.path.expanduser("~")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

