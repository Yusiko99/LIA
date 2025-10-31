from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class CommandType(str, Enum):
    """Types of commands that can be executed"""
    OPEN_FOLDER = "open_folder"
    OPEN_FILE = "open_file"
    LIST_FILES = "list_files"
    CREATE_FILE = "create_file"
    WRITE_FILE = "write_file"
    READ_FILE = "read_file"
    DELETE_FILE = "delete_file"
    SEARCH_FILES = "search_files"
    COPY_FILE = "copy_file"
    MOVE_FILE = "move_file"
    RENAME_FILE = "rename_file"
    GET_INFO = "get_info"
    EXECUTE_COMMAND = "execute_command"
    CHAT = "chat"  # General conversation mode
    HELP = "help"  # Show help and available commands
    UNKNOWN = "unknown"


class UserRequest(BaseModel):
    """User's natural language request"""
    message: str
    mode: str = "local"  # "local" (Ollama) or "general" (Gemini)
    thinking_mode: bool = False  # Enable thinking/reasoning mode


class CommandIntent(BaseModel):
    """Parsed command intent from LLM"""
    command_type: CommandType
    parameters: Dict[str, Any]
    original_message: str
    reasoning: Optional[str] = None


class CommandResult(BaseModel):
    """Result of command execution"""
    success: bool
    message: str
    data: Optional[Any] = None
    command_type: CommandType
    python_mode: Optional[bool] = False  # Indicates if Python mode was used
    python_code: Optional[str] = None  # The generated Python code (if applicable)


class ChatMessage(BaseModel):
    """Chat message in the UI"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    command_result: Optional[CommandResult] = None

