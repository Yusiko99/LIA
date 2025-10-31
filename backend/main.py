from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime
import logging
import json
import asyncio
import time
from collections import OrderedDict, deque

from models import UserRequest, CommandIntent, CommandResult, ChatMessage, CommandType
from ollama_service import OllamaService
from openrouter_service import OpenRouterService
from command_executor import CommandExecutor
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Local Intelligent Agent (LIA)",
    description="AI-powered local assistant with Ollama",
    version="2.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ollama_service = OllamaService()
openrouter_service = OpenRouterService()
command_executor = CommandExecutor()


# ----------------------
# In-memory Rate Limiter
# ----------------------
# Simple sliding window limiter: 10 requests / 30s per client (per endpoint group)
RATE_LIMIT_WINDOW_SEC = 30
RATE_LIMIT_MAX_REQUESTS = 10
_rate_limit_buckets = {}

def _allow_request(client_id: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SEC
    dq: deque = _rate_limit_buckets.setdefault(client_id, deque())
    # drop old
    while dq and dq[0] < window_start:
        dq.popleft()
    if len(dq) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    dq.append(now)
    return True


# ----------------------
# Tiny LRU Cache (with TTL)
# ----------------------
class LRUCacheTTL:
    def __init__(self, max_size: int = 256, ttl_sec: int = 120):
        self.max_size = max_size
        self.ttl = ttl_sec
        self.store: OrderedDict[str, tuple[float, object]] = OrderedDict()

    def get(self, key: str):
        item = self.store.get(key)
        if not item:
            return None
        ts, value = item
        if time.time() - ts > self.ttl:
            # expired
            try:
                del self.store[key]
            except KeyError:
                pass
            return None
        # move to end (recent)
        self.store.move_to_end(key)
        return value

    def set(self, key: str, value):
        self.store[key] = (time.time(), value)
        self.store.move_to_end(key)
        if len(self.store) > self.max_size:
            self.store.popitem(last=False)


intent_cache = LRUCacheTTL(max_size=256, ttl_sec=180)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Local Intelligent Agent (LIA)",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "local_model": {
            "host": settings.ollama_host,
            "model": settings.ollama_model,
            "available_models": settings.available_ollama_models
        },
        "general_model": {
            "provider": "OpenRouter",
            "model": settings.openrouter_model,
            "configured": bool(settings.openrouter_api_key),
            "available_models": settings.available_models
        }
    }

@app.get("/api/models")
async def get_available_models():
    """Get available models for both local and general modes"""
    return {
        "local_models": settings.available_ollama_models,
        "general_models": settings.available_models,
        "current_local": settings.ollama_model,
        "current_general": settings.openrouter_model
    }

@app.post("/api/models/switch")
async def switch_model(request: dict):
    """Switch the active model"""
    try:
        mode = request.get("mode")  # "local" or "general"
        model_id = request.get("model_id")
        
        if mode == "local":
            # Update Ollama model
            settings.ollama_model = model_id
            logger.info(f"Switched to local model: {model_id}")
            return {"success": True, "message": f"Switched to local model: {model_id}"}
        
        elif mode == "general":
            # Update OpenRouter model
            settings.openrouter_model = model_id
            logger.info(f"Switched to general model: {model_id}")
            return {"success": True, "message": f"Switched to general model: {model_id}"}
        
        else:
            return {"success": False, "message": "Invalid mode. Use 'local' or 'general'"}
    
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        return {"success": False, "message": f"Error switching model: {str(e)}"}


@app.post("/api/chat", response_model=ChatMessage)
async def process_chat(request: UserRequest, http_request: Request):
    """
    Process user's natural language request
    
    1. Parse intent using selected AI service (Local/Ollama or General/Gemini)
    2. Execute command safely
    3. Return result
    """
    try:
        # Rate limit
        client_ip = http_request.client.host if http_request.client else "unknown"
        if not _allow_request(f"chat:{client_ip}"):
            raise HTTPException(status_code=429, detail="Too many requests, please slow down.")

        logger.info(f"Processing request in {request.mode} mode: {request.message}")
        
        # Step 1: Parse user intent using selected service
        cache_key = f"{request.mode}:{request.message.strip()}"
        intent: CommandIntent | None = intent_cache.get(cache_key)
        if not intent:
            if request.mode == "general":
                intent = await openrouter_service.parse_user_intent(request.message)
            else:  # default to local
                intent = await ollama_service.parse_user_intent(request.message)
            intent_cache.set(cache_key, intent)
        
        logger.info(f"Parsed intent: {intent.command_type} with params: {intent.parameters}")
        
        # Step 2: Execute command (use appropriate service for AI generation)
        if request.mode == "general":
            command_executor.ollama_service = openrouter_service
        else:
            command_executor.ollama_service = ollama_service
            
        result: CommandResult = await command_executor.execute(intent)
        logger.info(f"Command result: success={result.success}, message={result.message}")
        
        # Step 3: Create chat response
        response = ChatMessage(
            role="assistant",
            content=result.message,
            timestamp=datetime.now().isoformat(),
            command_result=result
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_content(request: UserRequest, http_request: Request):
    """
    Generate content using Ollama (for creative tasks)
    """
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        if not _allow_request(f"gen:{client_ip}"):
            raise HTTPException(status_code=429, detail="Too many requests, please slow down.")
        content = await ollama_service.generate_content(request.message)
        return {
            "success": True,
            "content": content
        }
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream/v2")
async def stream_chat_v2(request: UserRequest, http_request: Request):
    """
    Stream chat with token-by-token streaming from LLM (typewriter effect)
    """
    async def generate_token_stream():
        try:
            client_ip = http_request.client.host if http_request.client else "unknown"
            if not _allow_request(f"streamv2:{client_ip}"):
                yield f"data: {json.dumps({'type': 'error', 'message': 'Too many requests'})}\n\n"
                return
            
            logger.info(f"Streaming v2 request in {request.mode} mode: {request.message}")
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing...'})}\n\n"
            await asyncio.sleep(0.05)
            
            # Parse intent (cached)
            cache_key = f"{request.mode}:{request.message.strip()}"
            intent = intent_cache.get(cache_key)
            if not intent:
                if request.mode == "general":
                    intent = await openrouter_service.parse_user_intent(request.message)
                else:
                    intent = await ollama_service.parse_user_intent(request.message)
                intent_cache.set(cache_key, intent)
            
            # Send intent
            yield f"data: {json.dumps({'type': 'intent', 'data': {'command_type': intent.command_type, 'reasoning': intent.reasoning}})}\n\n"
            await asyncio.sleep(0.05)
            
            # For CHAT commands, stream tokens from LLM
            if intent.command_type == CommandType.CHAT:
                prompt = intent.parameters.get("question", request.message)
                
                service = openrouter_service if request.mode == "general" else ollama_service
                
                # Stream tokens
                async for chunk in service.generate_content_stream(prompt, thinking_mode=request.thinking_mode):
                    if chunk["type"] == "token" and chunk["content"]:
                        # Only send non-empty tokens
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk['content']})}\n\n"
                    elif chunk["type"] == "thinking" and chunk["content"]:
                        yield f"data: {json.dumps({'type': 'thinking', 'content': chunk['content']})}\n\n"
                    elif chunk["type"] == "error":
                        yield f"data: {json.dumps({'type': 'error', 'message': chunk['content']})}\n\n"
                        return
                    
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.001)
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            else:
                # For non-chat commands, execute normally and send result
                if request.mode == "general":
                    command_executor.ollama_service = openrouter_service
                else:
                    command_executor.ollama_service = ollama_service
                
                result = await command_executor.execute(intent)
                
                response_data = {
                    'type': 'result',
                    'data': {
                        'role': 'assistant',
                        'content': result.message,
                        'timestamp': datetime.now().isoformat(),
                        'command_result': {
                            'success': result.success,
                            'message': result.message,
                            'data': result.data,
                            'command_type': result.command_type
                        }
                    }
                }
                yield f"data: {json.dumps(response_data)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
        except Exception as e:
            logger.error(f"Streaming v2 error: {e}", exc_info=True)
            error_data = {'type': 'error', 'message': str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_token_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/chat/stream")
async def stream_chat(request: UserRequest, http_request: Request):
    """
    Stream chat responses for better UX (Server-Sent Events)
    """
    async def generate_stream():
        try:
            client_ip = http_request.client.host if http_request.client else "unknown"
            if not _allow_request(f"stream:{client_ip}"):
                yield f"data: {json.dumps({'type': 'error', 'message': 'Too many requests'})}\n\n"
                return
            logger.info(f"Streaming request in {request.mode} mode: {request.message}")
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Parse intent
            cache_key = f"{request.mode}:{request.message.strip()}"
            intent = intent_cache.get(cache_key)
            if not intent:
                if request.mode == "general":
                    intent = await openrouter_service.parse_user_intent(request.message)
                else:
                    intent = await ollama_service.parse_user_intent(request.message)
                intent_cache.set(cache_key, intent)
            
            # Send intent info
            yield f"data: {json.dumps({'type': 'intent', 'data': {'command_type': intent.command_type, 'reasoning': intent.reasoning}})}\n\n"
            await asyncio.sleep(0.1)
            
            # Execute command
            if request.mode == "general":
                command_executor.ollama_service = openrouter_service
            else:
                command_executor.ollama_service = ollama_service
                
            result = await command_executor.execute(intent)
            
            # Send result
            response_data = {
                'type': 'result',
                'data': {
                    'role': 'assistant',
                    'content': result.message,
                    'timestamp': datetime.now().isoformat(),
                    'command_result': {
                        'success': result.success,
                        'message': result.message,
                        'data': result.data,
                        'command_type': result.command_type
                    }
                }
            }
            yield f"data: {json.dumps(response_data)}\n\n"
            
            # Send done signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_data = {
                'type': 'error',
                'message': str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )

