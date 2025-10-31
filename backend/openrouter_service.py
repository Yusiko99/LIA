import httpx
import json
from typing import Dict, Any
from config import settings
from models import CommandType, CommandIntent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenRouterService:
    """Service for interacting with OpenRouter API"""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Update API key from environment if available
        import os
        env_api_key = os.getenv('OPENROUTER_API_KEY')
        if env_api_key:
            self.api_key = env_api_key
        
    async def parse_user_intent(self, user_message: str) -> CommandIntent:
        """
        Parse user's natural language request into structured command intent using OpenRouter
        """
        
        # Create a detailed prompt for the LLM
        system_prompt = """You are LIA (Local Intelligent Agent), a file system assistant that can perform file operations and answer questions.

CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text.

Analyze the user's request and return a JSON response with this EXACT structure:

{
    "command_type": "open_folder|open_file|list_files|create_file|write_file|read_file|delete_file|search_files|copy_file|move_file|rename_file|get_info|execute_command|chat|help|unknown",
    "parameters": {
        "path": "file or folder path if needed",
        "pattern": "search pattern if needed", 
        "content": "content to write if needed",
        "filename": "filename to create if needed",
        "source": "source path for copy/move",
        "destination": "destination path for copy/move", 
        "new_name": "new name for rename",
        "command": "shell command to execute",
        "question": "question for chat mode"
    },
    "reasoning": "brief explanation"
}

FILE OPERATION EXAMPLES:
- "create gaus.txt file" -> {"command_type": "create_file", "parameters": {"filename": "gaus.txt"}, "reasoning": "User wants to create gaus.txt file"}
- "make notes.txt" -> {"command_type": "create_file", "parameters": {"filename": "notes.txt"}, "reasoning": "User wants to create notes.txt"}
- "open Downloads folder" -> {"command_type": "open_folder", "parameters": {"path": "Downloads"}, "reasoning": "User wants to open Downloads"}
- "list files in Documents" -> {"command_type": "list_files", "parameters": {"path": "Documents"}, "reasoning": "User wants to list files"}
- "search about gaussian and make gaus.txt" -> {"command_type": "create_file", "parameters": {"filename": "gaus.txt", "content": "Gaussian elimination information"}, "reasoning": "User wants to create gaus.txt with Gaussian content"}

CHAT EXAMPLES:
- "What is Python?" -> {"command_type": "chat", "parameters": {"question": "What is Python?"}, "reasoning": "User is asking a question"}
- "Explain machine learning" -> {"command_type": "chat", "parameters": {"question": "Explain machine learning"}, "reasoning": "User wants explanation"}

RESPOND WITH ONLY THE JSON OBJECT. NO OTHER TEXT."""

        user_prompt = f"User request: {user_message}\n\nJSON response:"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:5173",
                        "X-Title": "LIA - Local Intelligent Agent"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1024
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract the response text from OpenRouter's response structure
                # Grok model may return response in 'reasoning' field
                message = result["choices"][0]["message"]
                response_text = message.get("content", "")
                
                # If content is empty, check for reasoning field (Grok models use this)
                if not response_text and "reasoning" in message:
                    response_text = message["reasoning"]
                
                logger.info(f"OpenRouter Response: {response_text}")
                
                # Try to parse JSON from the response with multiple fallback strategies
                parsed = None
                
                # Strategy 1: Direct JSON parsing
                try:
                    parsed = json.loads(response_text.strip())
                except json.JSONDecodeError:
                    pass
                
                # Strategy 2: Clean markdown code blocks
                if not parsed:
                    try:
                        cleaned_response = response_text.strip()
                        # Remove various markdown patterns
                        for pattern in ["```json", "```", "`"]:
                            if cleaned_response.startswith(pattern):
                                cleaned_response = cleaned_response[len(pattern):]
                            if cleaned_response.endswith(pattern):
                                cleaned_response = cleaned_response[:-len(pattern)]
                        cleaned_response = cleaned_response.strip()
                        parsed = json.loads(cleaned_response)
                    except json.JSONDecodeError:
                        pass
                
                # Strategy 3: Extract JSON from text
                if not parsed:
                    try:
                        import re
                        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                        if json_match:
                            parsed = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # Strategy 4: Smart fallback based on keywords
                if not parsed:
                    logger.warning(f"Failed to parse OpenRouter response, using smart fallback: {response_text[:100]}...")
                    return self._smart_fallback_parse(user_message, response_text)
                
                # Validate parsed JSON
                if not isinstance(parsed, dict) or "command_type" not in parsed:
                    logger.warning(f"Invalid JSON structure, using smart fallback: {parsed}")
                    return self._smart_fallback_parse(user_message, response_text)
                
                return CommandIntent(
                    command_type=CommandType(parsed.get("command_type", "unknown")),
                    parameters=parsed.get("parameters", {}),
                    original_message=user_message,
                    reasoning=parsed.get("reasoning", "")
                )
                    
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            # Fallback: treat as chat
            return CommandIntent(
                command_type=CommandType.CHAT,
                parameters={"question": user_message},
                original_message=user_message,
                reasoning=f"Error: {str(e)}"
            )
    
    async def generate_content_stream(self, prompt: str, max_tokens: int = 2000, thinking_mode: bool = False):
        """
        Generate content with token-by-token streaming (async generator)
        """
        if not self.api_key:
            yield {"type": "error", "content": "OpenRouter API key not configured"}
            return
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:5173",
                        "X-Title": "LIA - Local Intelligent Agent"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": max_tokens,
                        "stream": True
                    }
                ) as response:
                    response.raise_for_status()
                    buffer = ""
                    async for chunk in response.aiter_text():
                        if not chunk:
                            continue
                        buffer += chunk
                        
                        # Process complete lines
                        lines = buffer.split("\n")
                        buffer = lines[-1]  # Keep incomplete line in buffer
                        
                        for line in lines[:-1]:
                            line = line.strip()
                            if not line or line == "data: [DONE]":
                                continue
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        reasoning = delta.get("reasoning", "")
                                        
                                        if thinking_mode and reasoning:
                                            yield {"type": "thinking", "content": reasoning}
                                        if content:
                                            yield {"type": "token", "content": content}
                                except json.JSONDecodeError as e:
                                    logger.debug(f"JSON parse error: {e}, line: {line[:100]}")
                                    pass
        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            yield {"type": "error", "content": str(e)}

    async def generate_content(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Generate content using OpenRouter (for writing file contents, chat responses, etc.)
        """
        if not self.api_key:
            return "OpenRouter API key not configured. Please run ./setup.sh to configure your API key."
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:5173",
                        "X-Title": "LIA - Local Intelligent Agent"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": max_tokens
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract the response text
                # Grok model may return response in 'reasoning' field
                message = result["choices"][0]["message"]
                response_text = message.get("content", "")
                
                # If content is empty, check for reasoning field (Grok models use this)
                if not response_text and "reasoning" in message:
                    response_text = message["reasoning"]
                
                return response_text
                
        except Exception as e:
            logger.error(f"OpenRouter content generation error: {e}")
            return f"Error generating content: {str(e)}"
    
    def _smart_fallback_parse(self, user_message: str, response_text: str) -> CommandIntent:
        """
        Smart fallback parsing when JSON parsing fails
        """
        message_lower = user_message.lower()
        
        # File creation patterns
        create_patterns = [
            "create", "make", "new file", "add file", "write file", "generate file",
            "yeni fayl", "yarat", "əlavə et"  # Azerbaijani
        ]
        
        if any(pattern in message_lower for pattern in create_patterns):
            # Extract filename from the message
            import re
            filename_match = re.search(r'(\w+\.\w+)', user_message)
            if filename_match:
                filename = filename_match.group(1)
                return CommandIntent(
                    command_type=CommandType.CREATE_FILE,
                    parameters={"filename": filename},
                    original_message=user_message,
                    reasoning="Smart fallback: detected file creation request"
                )
            else:
                # Try to extract any word that might be a filename
                words = user_message.split()
                for word in words:
                    if '.' in word and len(word) > 2:
                        return CommandIntent(
                            command_type=CommandType.CREATE_FILE,
                            parameters={"filename": word},
                            original_message=user_message,
                            reasoning="Smart fallback: extracted filename from message"
                        )
        
        # Folder operations
        if any(word in message_lower for word in ["open", "show", "list", "folder", "directory"]):
            return CommandIntent(
                command_type=CommandType.LIST_FILES,
                parameters={"path": "."},
                original_message=user_message,
                reasoning="Smart fallback: detected folder operation"
            )
        
        # Default to chat
        return CommandIntent(
            command_type=CommandType.CHAT,
            parameters={"question": user_message},
            original_message=user_message,
            reasoning="Smart fallback: treating as chat"
        )

