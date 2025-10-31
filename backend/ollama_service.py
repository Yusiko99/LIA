import httpx
import json
from typing import Dict, Any
from config import settings
from models import CommandType, CommandIntent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama LLM"""
    
    def __init__(self):
        self.base_url = settings.ollama_host
        self.model = settings.ollama_model
        
    async def parse_user_intent(self, user_message: str) -> CommandIntent:
        """
        Parse user's natural language request into structured command intent
        """
        
        # Create a detailed prompt for the LLM
        system_prompt = """You are a helpful AI assistant that interprets user commands for a local file system assistant.
Your task is to analyze the user's request and return a JSON response with the following structure:

{
           "command_type": "one of: open_folder, open_file, list_files, create_file, write_file, read_file, delete_file, search_files, copy_file, move_file, rename_file, get_info, execute_command, chat, help, unknown",
    "parameters": {
        "path": "optional: file or folder path",
        "pattern": "optional: search pattern or file extension",
        "content": "optional: content to write",
        "filename": "optional: name of file to create",
        "source": "optional: source path for copy/move",
        "destination": "optional: destination path for copy/move",
        "new_name": "optional: new name for rename",
        "command": "optional: shell command to execute",
        "question": "optional: for chat mode, the user's question"
    },
    "reasoning": "brief explanation of your interpretation"
}

IMPORTANT: If the user is asking a question, requesting information, or having a conversation (not performing a file operation), use command_type "chat" with the "question" parameter.

Examples:
- "Open the Pictures folder" -> {"command_type": "open_folder", "parameters": {"path": "Pictures"}, "reasoning": "User wants to open Pictures folder"}
- "List all PDF files in Downloads" -> {"command_type": "list_files", "parameters": {"path": "Downloads", "pattern": "*.pdf"}, "reasoning": "User wants to list PDF files"}
- "list all photo files in Downloads" -> {"command_type": "list_files", "parameters": {"path": "Downloads", "pattern": "*.{jpg,jpeg,png,gif}"}, "reasoning": "User wants to list photo files"}
- "Create a file called notes.txt" -> {"command_type": "create_file", "parameters": {"filename": "notes.txt"}, "reasoning": "User wants to create a text file"}
- "Yusif.txt adli fayl yarat" -> {"command_type": "create_file", "parameters": {"filename": "Yusif.txt"}, "reasoning": "User wants to create a file (Azerbaijani: 'create file named Yusif.txt')"}
- "fayl yarat notes.txt" -> {"command_type": "create_file", "parameters": {"filename": "notes.txt"}, "reasoning": "User wants to create a file (Azerbaijani)"}
- "Delete old.txt" -> {"command_type": "delete_file", "parameters": {"path": "old.txt"}, "reasoning": "User wants to delete a file"}
- "What is Python?" -> {"command_type": "chat", "parameters": {"question": "What is Python?"}, "reasoning": "User is asking a question"}
- "Tell me about yourself" -> {"command_type": "chat", "parameters": {"question": "Tell me about yourself"}, "reasoning": "User wants to have a conversation"}
- "How does machine learning work?" -> {"command_type": "chat", "parameters": {"question": "How does machine learning work?"}, "reasoning": "User is asking for information"}

Only respond with valid JSON, no additional text."""

        prompt = f"{system_prompt}\n\nUser request: {user_message}\n\nJSON response:"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.3,
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract the response text
                response_text = result.get("response", "")
                logger.info(f"LLM Response: {response_text}")
                
                # Try to parse JSON from the response
                try:
                    # Clean up the response - sometimes LLMs add markdown code blocks
                    cleaned_response = response_text.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:]
                    if cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:]
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()
                    
                    parsed = json.loads(cleaned_response)
                    
                    return CommandIntent(
                        command_type=CommandType(parsed.get("command_type", "unknown")),
                        parameters=parsed.get("parameters", {}),
                        original_message=user_message,
                        reasoning=parsed.get("reasoning", "")
                    )
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse LLM response: {e}")
                    # Fallback: try to infer from keywords
                    return self._fallback_parse(user_message)
                    
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return self._fallback_parse(user_message)
    
    def _fallback_parse(self, message: str) -> CommandIntent:
        """Fallback parsing using simple keyword matching"""
        message_lower = message.lower()
        
        # Check for help requests first
        help_indicators = [
            "help", "commands", "what can you do", "show me", "list commands",
            "available commands", "how to", "guide", "tutorial", "manual",
            "yardım", "komandalar", "nə edə bilərsən"  # Azerbaijani help words
        ]
        
        if any(indicator in message_lower for indicator in help_indicators):
            return CommandIntent(
                command_type=CommandType.HELP,
                parameters={"help_type": "general"},
                original_message=message,
                reasoning="Fallback: detected help request"
            )
        
        # Check for questions/conversations
        question_indicators = [
            "what", "why", "how", "when", "where", "who",
            "tell me", "explain", "describe", "can you",
            "do you know", "?", "nədir", "necə", "niyə"  # Azerbaijani question words
        ]
        
        if any(indicator in message_lower for indicator in question_indicators):
            # Check if it's actually a command disguised as a question
            command_keywords = ["open", "list", "create", "delete", "copy", "move", "rename", "show", "display"]
            has_command = any(cmd in message_lower for cmd in command_keywords)
            
            # If no clear command keywords, treat as chat
            if not has_command:
                return CommandIntent(
                    command_type=CommandType.CHAT,
                    parameters={"question": message},
                    original_message=message,
                    reasoning="Fallback: detected question/conversation"
                )
        
        if "open" in message_lower or "aç" in message_lower:
            # Extract path
            words = message.split()
            path = "~"
            for word in words:
                if word.lower() not in ["open", "the", "folder", "directory", "file"]:
                    path = word
                    break
            
            # Check if it's a file or folder
            if any(ext in message_lower for ext in [".jpg", ".png", ".pdf", ".txt", ".doc", ".mp4", ".mp3"]):
                return CommandIntent(
                    command_type=CommandType.OPEN_FILE,
                    parameters={"path": path},
                    original_message=message,
                    reasoning="Fallback: detected file open request"
                )
            else:
                return CommandIntent(
                    command_type=CommandType.OPEN_FOLDER,
                    parameters={"path": path},
                    original_message=message,
                    reasoning="Fallback: detected folder open request"
                )
            
        elif "list" in message_lower or "show" in message_lower or "göstər" in message_lower:
            path = "."
            pattern = "*"
            if "pdf" in message_lower:
                pattern = "*.pdf"
            elif "image" in message_lower or "photo" in message_lower or "picture" in message_lower or "jpg" in message_lower or "png" in message_lower or "şəkil" in message_lower:
                pattern = "*.{jpg,png,jpeg,gif,bmp,webp,JPG,PNG,JPEG}"
            if "downloads" in message_lower or "yükləmələr" in message_lower:
                path = "Downloads"
            elif "documents" in message_lower or "sənədlər" in message_lower:
                path = "Documents"
            elif "pictures" in message_lower or "şəkillər" in message_lower:
                path = "Pictures"
                
            return CommandIntent(
                command_type=CommandType.LIST_FILES,
                parameters={"path": path, "pattern": pattern},
                original_message=message,
                reasoning="Fallback: detected file listing request"
            )
        
        elif "delete" in message_lower or "remove" in message_lower:
            words = message.split()
            path = None
            for word in words:
                if word.lower() not in ["delete", "remove", "the", "file"]:
                    path = word
                    break
            
            return CommandIntent(
                command_type=CommandType.DELETE_FILE,
                parameters={"path": path or ""},
                original_message=message,
                reasoning="Fallback: detected delete request"
            )
        
        elif "copy" in message_lower:
            words = message.split()
            source = None
            dest = None
            for i, word in enumerate(words):
                if word.lower() == "copy" and i + 1 < len(words):
                    source = words[i + 1]
                if word.lower() == "to" and i + 1 < len(words):
                    dest = words[i + 1]
            
            return CommandIntent(
                command_type=CommandType.COPY_FILE,
                parameters={"source": source or "", "destination": dest or ""},
                original_message=message,
                reasoning="Fallback: detected copy request"
            )
        
        elif "rename" in message_lower:
            words = message.split()
            path = None
            new_name = None
            for i, word in enumerate(words):
                if word.lower() == "rename" and i + 1 < len(words):
                    path = words[i + 1]
                if word.lower() == "to" and i + 1 < len(words):
                    new_name = words[i + 1]
            
            return CommandIntent(
                command_type=CommandType.RENAME_FILE,
                parameters={"path": path or "", "new_name": new_name or ""},
                original_message=message,
                reasoning="Fallback: detected rename request"
            )
            
        elif "create" in message_lower or "yarat" in message_lower or "fayl" in message_lower:
            # Try to extract filename - handle multiple languages
            words = message.split()
            filename = "newfile.txt"
            
            # Look for filename patterns
            for i, word in enumerate(words):
                # Check if word looks like a filename (has extension)
                if "." in word and not word.startswith("."):
                    filename = word.strip('",\'')
                    break
                # Check for keywords that precede filename
                if word.lower() in ["named", "called", "name", "adli", "adlı"] and i + 1 < len(words):
                    filename = words[i + 1].strip('",\'')
                    break
                    
            return CommandIntent(
                command_type=CommandType.CREATE_FILE,
                parameters={"filename": filename},
                original_message=message,
                reasoning="Fallback: detected file creation request"
            )
        
        # For unknown commands, mark them as potential Python tasks
        return CommandIntent(
            command_type=CommandType.UNKNOWN,
            parameters={"original_request": message},
            original_message=message,
            reasoning="Could not determine command type - will try Python fallback"
        )
    
    async def generate_content_stream(self, prompt: str, max_tokens: int = 2000, thinking_mode: bool = False):
        """
        Generate content with token-by-token streaming (async generator)
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": True,
                    }
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                token = data.get("response", "")
                                if token:
                                    yield {"type": "token", "content": token}
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield {"type": "error", "content": str(e)}

    async def generate_content(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Generate content using Ollama (for writing file contents, etc.)
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
                
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return f"Error generating content: {str(e)}"

