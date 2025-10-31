import os
import subprocess
import glob
import shutil
from pathlib import Path
from typing import List, Dict, Any
import logging
import platform
from models import CommandIntent, CommandResult, CommandType
from ollama_service import OllamaService
from python_executor import PythonExecutor
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandExecutor:
    """Safely execute system commands based on parsed intents"""
    
    def __init__(self):
        self.ollama_service = OllamaService()
        self.python_executor = None  # Lazy initialization
        self.allowed_base_dir = os.path.expanduser(settings.allowed_directories)
        
    def _normalize_path(self, path: str) -> Path:
        """Normalize and validate path for security"""
        # Handle common folder names
        common_folders = {
            "downloads": "Downloads",
            "documents": "Documents",
            "pictures": "Pictures",
            "desktop": "Desktop",
            "music": "Music",
            "videos": "Videos",
            "home": "",
        }
        
        path_lower = path.lower().strip()
        
        # If it's a common folder name without path separator, prepend home
        if path_lower in common_folders and "/" not in path and "\\" not in path:
            folder_name = common_folders[path_lower]
            if folder_name:
                path = f"~/{folder_name}"
            else:
                path = "~"
        
        # Expand ~ and relative paths
        expanded = os.path.expanduser(path)
        normalized = Path(expanded).resolve()
        
        # Security check: ensure path is within allowed directories
        base = Path(self.allowed_base_dir).resolve()
        try:
            normalized.relative_to(base)
        except ValueError:
            raise PermissionError(f"Access denied: {path} is outside allowed directories")
        
        return normalized
    
    def _ensure_python_executor(self):
        """Lazy initialization of Python executor"""
        if self.python_executor is None:
            self.python_executor = PythonExecutor(self.ollama_service)
    
    async def _try_python_fallback(self, intent: CommandIntent, original_error: str = None) -> CommandResult:
        """
        Attempt to execute the request using Python code generation and execution.
        This is called when native commands fail or aren't suitable.
        """
        self._ensure_python_executor()
        
        # Check if Python can handle this request
        can_handle = await self.python_executor.can_handle_with_python(
            intent.original_message,
            str(intent.command_type)
        )
        
        if not can_handle:
            # Python can't help, return the original error
            return CommandResult(
                success=False,
                message=original_error or "Unable to execute request",
                command_type=intent.command_type,
                python_mode=False
            )
        
        logger.info(f"Attempting Python fallback for: {intent.original_message}")
        
        # Execute with Python
        result = await self.python_executor.execute_with_python(
            intent.original_message,
            context={'intent': intent.command_type, 'parameters': intent.parameters}
        )
        
        return CommandResult(
            success=result['success'],
            message=result['message'],
            data={
                'output': result.get('output', ''),
                'error': result.get('error'),
                'python_code': result.get('code', '')
            },
            command_type=intent.command_type,
            python_mode=True,
            python_code=result.get('code', '')
        )
    
    async def execute(self, intent: CommandIntent) -> CommandResult:
        """Execute command based on intent"""
        
        try:
            if intent.command_type == CommandType.OPEN_FOLDER:
                return await self._open_folder(intent.parameters)
            
            elif intent.command_type == CommandType.OPEN_FILE:
                return await self._open_file(intent.parameters)
            
            elif intent.command_type == CommandType.LIST_FILES:
                return await self._list_files(intent.parameters)
            
            elif intent.command_type == CommandType.CREATE_FILE:
                return await self._create_file(intent.parameters)
            
            elif intent.command_type == CommandType.WRITE_FILE:
                return await self._write_file(intent.parameters)
            
            elif intent.command_type == CommandType.READ_FILE:
                return await self._read_file(intent.parameters)
            
            elif intent.command_type == CommandType.DELETE_FILE:
                return await self._delete_file(intent.parameters)
            
            elif intent.command_type == CommandType.SEARCH_FILES:
                return await self._search_files(intent.parameters)
            
            elif intent.command_type == CommandType.COPY_FILE:
                return await self._copy_file(intent.parameters)
            
            elif intent.command_type == CommandType.MOVE_FILE:
                return await self._move_file(intent.parameters)
            
            elif intent.command_type == CommandType.RENAME_FILE:
                return await self._rename_file(intent.parameters)
            
            elif intent.command_type == CommandType.GET_INFO:
                return await self._get_info(intent.parameters)
            
            elif intent.command_type == CommandType.EXECUTE_COMMAND:
                return await self._execute_command(intent.parameters)
            
            elif intent.command_type == CommandType.CHAT:
                return await self._chat(intent.parameters)
            
            elif intent.command_type == CommandType.HELP:
                return await self._help(intent.parameters)
            
            else:
                # ALWAYS try Python fallback for unknown commands
                logger.info(f"Unknown command type, automatically using Python fallback")
                self._ensure_python_executor()
                
                # Execute with Python directly (no "can_handle" check for unknowns)
                result = await self.python_executor.execute_with_python(
                    intent.original_message,
                    context={'intent': intent.command_type, 'parameters': intent.parameters}
                )
                
                return CommandResult(
                    success=result['success'],
                    message=result['message'],
                    data={
                        'output': result.get('output', ''),
                        'error': result.get('error'),
                        'python_code': result.get('code', '')
                    },
                    command_type=CommandType.UNKNOWN,
                    python_mode=True,
                    python_code=result.get('code', '')
                )
                
        except PermissionError as e:
            return CommandResult(
                success=False,
                message=f"Permission denied: {str(e)}",
                command_type=intent.command_type
            )
        except Exception as e:
            logger.error(f"Command execution error: {e}", exc_info=True)
            
            # Try Python fallback on errors
            error_message = str(e)
            
            # Check if this error could be resolved with Python
            if any(keyword in intent.original_message.lower() for keyword in 
                   ['calculate', 'average', 'sum', 'count', 'analyze', 'parse', 'extract']):
                logger.info(f"Command failed, attempting Python fallback due to computational nature")
                return await self._try_python_fallback(intent, error_message)
            
            return CommandResult(
                success=False,
                message=f"Error executing command: {error_message}",
                command_type=intent.command_type,
                python_mode=False
            )
    
    async def _open_folder(self, params: Dict[str, Any]) -> CommandResult:
        """Open a folder in the file manager"""
        path = params.get("path", "~")
        
        try:
            normalized_path = self._normalize_path(path)
            
            if not normalized_path.exists():
                return CommandResult(
                    success=False,
                    message=f"Folder not found: {path}",
                    command_type=CommandType.OPEN_FOLDER
                )
            
            if not normalized_path.is_dir():
                return CommandResult(
                    success=False,
                    message=f"Not a directory: {path}",
                    command_type=CommandType.OPEN_FOLDER
                )
            
            # Open folder based on OS
            system = platform.system()
            if system == "Linux":
                subprocess.Popen(["xdg-open", str(normalized_path)])
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", str(normalized_path)])
            elif system == "Windows":
                subprocess.Popen(["explorer", str(normalized_path)])
            else:
                return CommandResult(
                    success=False,
                    message=f"Unsupported operating system: {system}",
                    command_type=CommandType.OPEN_FOLDER
                )
            
            return CommandResult(
                success=True,
                message=f"Opened folder: {normalized_path}",
                data={"path": str(normalized_path)},
                command_type=CommandType.OPEN_FOLDER
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to open folder: {str(e)}",
                command_type=CommandType.OPEN_FOLDER
            )
    
    async def _open_file(self, params: Dict[str, Any]) -> CommandResult:
        """Open a file with default application"""
        path = params.get("path")
        
        if not path:
            return CommandResult(
                success=False,
                message="No file path specified",
                command_type=CommandType.OPEN_FILE
            )
        
        try:
            normalized_path = self._normalize_path(path)
            
            if not normalized_path.exists():
                return CommandResult(
                    success=False,
                    message=f"File not found: {path}",
                    command_type=CommandType.OPEN_FILE
                )
            
            if not normalized_path.is_file():
                return CommandResult(
                    success=False,
                    message=f"Not a file: {path}",
                    command_type=CommandType.OPEN_FILE
                )
            
            # Open file based on OS
            system = platform.system()
            if system == "Linux":
                subprocess.Popen(["xdg-open", str(normalized_path)])
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", str(normalized_path)])
            elif system == "Windows":
                os.startfile(str(normalized_path))
            else:
                return CommandResult(
                    success=False,
                    message=f"Unsupported operating system: {system}",
                    command_type=CommandType.OPEN_FILE
                )
            
            return CommandResult(
                success=True,
                message=f"Opened file: {normalized_path.name}",
                data={"path": str(normalized_path), "name": normalized_path.name},
                command_type=CommandType.OPEN_FILE
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to open file: {str(e)}",
                command_type=CommandType.OPEN_FILE
            )
    
    async def _list_files(self, params: Dict[str, Any]) -> CommandResult:
        """List files in a directory"""
        path = params.get("path", ".")
        pattern = params.get("pattern", "*")
        
        try:
            normalized_path = self._normalize_path(path)
            
            if not normalized_path.exists():
                return CommandResult(
                    success=False,
                    message=f"Directory not found: {path}",
                    command_type=CommandType.LIST_FILES
                )
            
            if not normalized_path.is_dir():
                return CommandResult(
                    success=False,
                    message=f"Not a directory: {path}",
                    command_type=CommandType.LIST_FILES
                )
            
            # List files matching pattern
            search_pattern = str(normalized_path / pattern)
            matching_files = glob.glob(search_pattern)
            
            # Get file info
            file_list = []
            for file_path in matching_files:
                p = Path(file_path)
                if p.is_file():
                    stat = p.stat()
                    file_list.append({
                        "name": p.name,
                        "path": str(p),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
            
            file_list.sort(key=lambda x: x["name"])
            
            return CommandResult(
                success=True,
                message=f"Found {len(file_list)} file(s) matching '{pattern}' in {normalized_path}",
                data={"files": file_list, "count": len(file_list)},
                command_type=CommandType.LIST_FILES
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to list files: {str(e)}",
                command_type=CommandType.LIST_FILES
            )
    
    async def _create_file(self, params: Dict[str, Any]) -> CommandResult:
        """Create a new file, optionally with AI-generated content"""
        filename = params.get("filename", "newfile.txt")
        content = params.get("content", "")
        
        try:
            # If filename doesn't have path, use current user's home or Documents
            if "/" not in filename and "\\" not in filename:
                base_dir = Path.home() / "Documents"
                base_dir.mkdir(exist_ok=True)
                file_path = base_dir / filename
            else:
                file_path = self._normalize_path(filename)
            
            # If content is a request for AI generation, generate it
            if content and any(keyword in content.lower() for keyword in ["write", "generate", "pages", "about", "search", "information", "content"]):
                logger.info(f"Generating content with AI for: {filename}")
                # Extract what to write about from the content or original message
                if "about" in content.lower() or "search" in content.lower():
                    # Extract the topic from the content
                    topic = content.lower().replace("about", "").replace("search", "").replace("information", "").strip()
                    prompt = f"Write comprehensive information about {topic}. Create detailed content that explains the topic clearly and thoroughly. Format it well with headings and explanations."
                else:
                    prompt = f"Write detailed content for a file. The request was: {content}. Generate appropriate content that would fill approximately 1-2 pages."
                
                generated_content = await self.ollama_service.generate_content(prompt, max_tokens=3000)
                content_to_write = generated_content
            elif content:
                content_to_write = content
            else:
                content_to_write = f"# {filename}\n\nCreated by Local Intelligent Agent\n"
            
            # Create the file
            file_path.write_text(content_to_write, encoding="utf-8")
            
            return CommandResult(
                success=True,
                message=f"Created file: {file_path}",
                data={
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "content_preview": content_to_write[:200] + "..." if len(content_to_write) > 200 else content_to_write
                },
                command_type=CommandType.CREATE_FILE
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to create file: {str(e)}",
                command_type=CommandType.CREATE_FILE
            )
    
    async def _write_file(self, params: Dict[str, Any]) -> CommandResult:
        """Write content to an existing file"""
        path = params.get("path")
        content = params.get("content", "")
        
        if not path:
            return CommandResult(
                success=False,
                message="No file path specified",
                command_type=CommandType.WRITE_FILE
            )
        
        try:
            file_path = self._normalize_path(path)
            file_path.write_text(content, encoding="utf-8")
            
            return CommandResult(
                success=True,
                message=f"Wrote content to: {file_path}",
                data={"path": str(file_path), "size": file_path.stat().st_size},
                command_type=CommandType.WRITE_FILE
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to write file: {str(e)}",
                command_type=CommandType.WRITE_FILE
            )
    
    async def _read_file(self, params: Dict[str, Any]) -> CommandResult:
        """Read file contents"""
        path = params.get("path")
        
        if not path:
            return CommandResult(
                success=False,
                message="No file path specified",
                command_type=CommandType.READ_FILE
            )
        
        try:
            file_path = self._normalize_path(path)
            
            if not file_path.exists():
                return CommandResult(
                    success=False,
                    message=f"File not found: {path}",
                    command_type=CommandType.READ_FILE
                )
            
            content = file_path.read_text(encoding="utf-8")
            
            return CommandResult(
                success=True,
                message=f"Read file: {file_path}",
                data={"path": str(file_path), "content": content},
                command_type=CommandType.READ_FILE
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to read file: {str(e)}",
                command_type=CommandType.READ_FILE
            )
    
    async def _search_files(self, params: Dict[str, Any]) -> CommandResult:
        """Search for files by name pattern"""
        pattern = params.get("pattern", "*")
        path = params.get("path", "~")
        
        try:
            normalized_path = self._normalize_path(path)
            
            # Recursive search
            matching_files = list(normalized_path.rglob(pattern))
            
            file_list = []
            for file_path in matching_files[:100]:  # Limit to 100 results
                if file_path.is_file():
                    stat = file_path.stat()
                    file_list.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
            
            return CommandResult(
                success=True,
                message=f"Found {len(file_list)} file(s) matching '{pattern}'",
                data={"files": file_list, "count": len(file_list)},
                command_type=CommandType.SEARCH_FILES
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to search files: {str(e)}",
                command_type=CommandType.SEARCH_FILES
            )
    
    async def _delete_file(self, params: Dict[str, Any]) -> CommandResult:
        """Delete a file"""
        path = params.get("path")
        
        if not path:
            return CommandResult(
                success=False,
                message="No file path specified",
                command_type=CommandType.DELETE_FILE
            )
        
        try:
            normalized_path = self._normalize_path(path)
            
            if not normalized_path.exists():
                return CommandResult(
                    success=False,
                    message=f"File not found: {path}",
                    command_type=CommandType.DELETE_FILE
                )
            
            if normalized_path.is_file():
                normalized_path.unlink()
                return CommandResult(
                    success=True,
                    message=f"Deleted file: {normalized_path.name}",
                    data={"path": str(normalized_path)},
                    command_type=CommandType.DELETE_FILE
                )
            elif normalized_path.is_dir():
                shutil.rmtree(normalized_path)
                return CommandResult(
                    success=True,
                    message=f"Deleted directory: {normalized_path.name}",
                    data={"path": str(normalized_path)},
                    command_type=CommandType.DELETE_FILE
                )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to delete: {str(e)}",
                command_type=CommandType.DELETE_FILE
            )
    
    async def _copy_file(self, params: Dict[str, Any]) -> CommandResult:
        """Copy a file or directory"""
        source = params.get("source")
        destination = params.get("destination")
        
        if not source or not destination:
            return CommandResult(
                success=False,
                message="Source and destination paths required",
                command_type=CommandType.COPY_FILE
            )
        
        try:
            source_path = self._normalize_path(source)
            dest_path = self._normalize_path(destination)
            
            if not source_path.exists():
                return CommandResult(
                    success=False,
                    message=f"Source not found: {source}",
                    command_type=CommandType.COPY_FILE
                )
            
            if source_path.is_file():
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copytree(source_path, dest_path)
            
            return CommandResult(
                success=True,
                message=f"Copied {source_path.name} to {dest_path}",
                data={"source": str(source_path), "destination": str(dest_path)},
                command_type=CommandType.COPY_FILE
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to copy: {str(e)}",
                command_type=CommandType.COPY_FILE
            )
    
    async def _move_file(self, params: Dict[str, Any]) -> CommandResult:
        """Move a file or directory"""
        source = params.get("source")
        destination = params.get("destination")
        
        if not source or not destination:
            return CommandResult(
                success=False,
                message="Source and destination paths required",
                command_type=CommandType.MOVE_FILE
            )
        
        try:
            source_path = self._normalize_path(source)
            dest_path = self._normalize_path(destination)
            
            if not source_path.exists():
                return CommandResult(
                    success=False,
                    message=f"Source not found: {source}",
                    command_type=CommandType.MOVE_FILE
                )
            
            shutil.move(str(source_path), str(dest_path))
            
            return CommandResult(
                success=True,
                message=f"Moved {source_path.name} to {dest_path}",
                data={"source": str(source_path), "destination": str(dest_path)},
                command_type=CommandType.MOVE_FILE
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to move: {str(e)}",
                command_type=CommandType.MOVE_FILE
            )
    
    async def _rename_file(self, params: Dict[str, Any]) -> CommandResult:
        """Rename a file or directory"""
        path = params.get("path")
        new_name = params.get("new_name")
        
        if not path or not new_name:
            return CommandResult(
                success=False,
                message="Path and new name required",
                command_type=CommandType.RENAME_FILE
            )
        
        try:
            source_path = self._normalize_path(path)
            
            if not source_path.exists():
                return CommandResult(
                    success=False,
                    message=f"File not found: {path}",
                    command_type=CommandType.RENAME_FILE
                )
            
            dest_path = source_path.parent / new_name
            source_path.rename(dest_path)
            
            return CommandResult(
                success=True,
                message=f"Renamed {source_path.name} to {new_name}",
                data={"old_path": str(source_path), "new_path": str(dest_path)},
                command_type=CommandType.RENAME_FILE
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to rename: {str(e)}",
                command_type=CommandType.RENAME_FILE
            )
    
    async def _execute_command(self, params: Dict[str, Any]) -> CommandResult:
        """Execute a safe shell command"""
        command = params.get("command", "")
        
        # Comprehensive whitelist of safe commands (100+ commands)
        safe_commands = [
            # File and Directory Operations
            "ls", "pwd", "cd", "mkdir", "rmdir", "touch", "cat", "head", "tail", "less", "more",
            "wc", "sort", "uniq", "grep", "find", "locate", "which", "whereis", "file", "stat",
            "du", "df", "mount", "umount", "chmod", "chown", "chgrp", "ln", "readlink",
            
            # Text Processing and Search
            "awk", "sed", "cut", "paste", "join", "diff", "cmp", "comm", "tr", "expand", "unexpand",
            "fold", "fmt", "pr", "column", "nl", "tac", "rev", "base64", "hexdump", "od",
            
            # System Information
            "uname", "hostname", "whoami", "id", "groups", "who", "w", "users", "last", "lastlog",
            "uptime", "date", "cal", "time", "env", "printenv", "set", "ps", "top", "htop",
            "free", "vmstat", "iostat", "sar", "netstat", "ss", "lsof", "fuser", "lscpu", "lsmem",
            
            # Network and Connectivity
            "ping", "traceroute", "nslookup", "dig", "host", "curl", "wget", "nc", "telnet",
            "ssh", "scp", "rsync", "ifconfig", "ip", "route", "arp", "iptables", "ufw",
            
            # Process Management
            "kill", "killall", "pkill", "pgrep", "jobs", "bg", "fg", "nohup", "screen", "tmux",
            "at", "crontab", "systemctl", "service", "initctl",
            
            # Archive and Compression
            "tar", "gzip", "gunzip", "bzip2", "bunzip2", "xz", "unxz", "zip", "unzip", "7z",
            "rar", "unrar", "cpio", "ar", "zipinfo",
            
            # Package Management
            "apt", "apt-get", "apt-cache", "dpkg", "yum", "dnf", "rpm", "pacman", "brew",
            "pip", "npm", "yarn", "gem", "cargo", "go", "maven", "gradle",
            
            # Development Tools
            "git", "svn", "hg", "make", "cmake", "gcc", "g++", "clang", "python", "python3",
            "node", "npm", "yarn", "java", "javac", "javadoc", "mvn", "gradle", "docker",
            "docker-compose", "kubectl", "helm", "terraform", "ansible",
            
            # Monitoring and Logging
            "tail", "journalctl", "dmesg", "syslog", "logger", "watch", "strace", "ltrace",
            "tcpdump", "wireshark", "tcpflow", "ngrep", "iftop", "iotop", "nethogs",
            
            # Utilities and Tools
            "man", "info", "help", "type", "alias", "history", "clear", "reset", "stty",
            "tty", "mesg", "write", "wall", "talk", "finger", "whois", "wget", "curl",
            "lynx", "links", "elinks", "w3m", "tree", "exa", "bat", "fd", "ripgrep",
            
            # Mathematical and Scientific
            "bc", "dc", "factor", "primes", "seq", "shuf", "random", "expr", "let",
            
            # Miscellaneous
            "yes", "no", "true", "false", "echo", "printf", "sleep", "wait", "timeout",
            "nice", "renice", "ionice", "taskset", "chrt", "flock", "fuser", "lsof"
        ]
        
        # Check if command starts with a safe command
        cmd_parts = command.split()
        if not cmd_parts:
            return CommandResult(
                success=False,
                message="Empty command",
                command_type=CommandType.EXECUTE_COMMAND
            )
        
        base_command = cmd_parts[0]
        if base_command not in safe_commands:
            return CommandResult(
                success=False,
                message=f"Command not allowed. Safe commands: {', '.join(safe_commands)}",
                command_type=CommandType.EXECUTE_COMMAND
            )
        
        # Enhanced security: Dangerous patterns and commands to block
        dangerous_patterns = [
            # Destructive commands
            "rm ", "rm -", "del ", "format ", "mkfs", "dd if=", "dd of=", "shutdown", "reboot", "halt", "poweroff",
            "init 0", "init 6", "kill -9", "killall -9", "pkill -9",
            
            # System modification
            "chmod 777", "chmod +s", "chown root", "passwd", "useradd", "userdel", "groupadd", "groupdel",
            "usermod", "groupmod", "visudo", "sudo ", "su ", "sudoers",
            
            # Network security risks
            "nc -l", "netcat -l", "python -m http.server", "python3 -m http.server", "php -S",
            "ruby -run", "perl -MIO::Socket", "telnetd", "sshd", "ftp", "tftp",
            
            # File system risks
            "mount -o", "umount -f", "fdisk", "parted", "mkfs", "fsck", "badblocks",
            "dd if=/dev/", "dd of=/dev/", "cat > /dev/", "echo > /dev/",
            
            # Process and system risks
            "kill -STOP", "kill -CONT", "renice -20", "nice -20", "ionice -c 1",
            "taskset -c 0", "chrt -f 99", "strace -e trace", "ltrace -e",
            
            # Package and system modification
            "apt remove", "apt purge", "yum remove", "dnf remove", "pacman -R", "brew uninstall",
            "pip uninstall", "npm uninstall", "gem uninstall", "cargo uninstall",
            
            # Development risks
            "make install", "make uninstall", "cmake --install", "docker run --privileged",
            "docker exec --privileged", "kubectl delete", "helm uninstall", "terraform destroy",
            
            # Shell injection patterns
            "; rm", "; del", "; format", "; shutdown", "; reboot", "&& rm", "&& del",
            "|| rm", "|| del", "| rm", "| del", "> /dev/", ">> /dev/", "2> /dev/",
            
            # Script execution risks
            "bash -c", "sh -c", "zsh -c", "fish -c", "python -c", "perl -e", "ruby -e",
            "node -e", "php -r", "lua -e", "awk '{", "sed '", "eval", "exec",
            
            # Environment manipulation
            "export PATH=", "export LD_LIBRARY_PATH=", "export PYTHONPATH=", "alias rm=",
            "unalias", "hash -r", "builtin", "command", "type -a", "declare -f"
        ]
        
        # Check for dangerous patterns
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return CommandResult(
                    success=False,
                    message=f"🚫 Command blocked for security: Contains dangerous pattern '{pattern}'",
                    command_type=CommandType.EXECUTE_COMMAND
                )
        
        # For complex commands with pipes, use shell=True but with restrictions
        use_shell = "|" in command or ">" in command or "&&" in command or "||" in command
        
        try:
            if use_shell:
                
                # Enhanced logging for shell commands
                logger.info(f"Executing shell command: {command}")
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=15,  # Increased timeout for complex commands
                    cwd=os.path.expanduser("~")  # Set safe working directory
                )
            else:
                # Enhanced logging for simple commands
                logger.info(f"Executing command: {cmd_parts}")
                result = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    timeout=10,  # Increased timeout
                    cwd=os.path.expanduser("~")  # Set safe working directory
                )
            
            # Enhanced output processing
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if result.returncode == 0:
                if stdout:
                    # Truncate very long output for better UX
                    if len(stdout) > 2000:
                        truncated_output = stdout[:2000] + "\n\n... (output truncated, showing first 2000 characters)"
                        message = f"✅ {command}\n\n{truncated_output}"
                    else:
                        message = f"✅ {command}\n\n{stdout}"
                else:
                    message = f"✅ {command} (executed successfully)"
            else:
                # Enhanced error reporting
                error_msg = f"❌ Command failed (exit code {result.returncode}): {command}"
                if stderr:
                    error_msg += f"\n\nError details:\n{stderr}"
                if stdout:
                    error_msg += f"\n\nOutput:\n{stdout}"
                message = error_msg
            
            # Log the result
            logger.info(f"Command result: success={result.returncode == 0}, returncode={result.returncode}")
            
            return CommandResult(
                success=result.returncode == 0,
                message=message,
                data={
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": result.returncode,
                    "command": command,
                    "execution_time": "N/A"  # Could add timing in future
                },
                command_type=CommandType.EXECUTE_COMMAND
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                message=f"⏰ Command timed out: {command}",
                command_type=CommandType.EXECUTE_COMMAND
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"❌ Command failed: {str(e)}",
                command_type=CommandType.EXECUTE_COMMAND
            )
    
    async def _get_info(self, params: Dict[str, Any]) -> CommandResult:
        """Get system information"""
        path = params.get("path")
        
        if path:
            # Get info about specific file/directory
            try:
                normalized_path = self._normalize_path(path)
                if not normalized_path.exists():
                    return CommandResult(
                        success=False,
                        message=f"Path not found: {path}",
                        command_type=CommandType.GET_INFO
                    )
                
                stat = normalized_path.stat()
                info = {
                    "name": normalized_path.name,
                    "path": str(normalized_path),
                    "type": "file" if normalized_path.is_file() else "directory",
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "permissions": oct(stat.st_mode)[-3:],
                }
                
                return CommandResult(
                    success=True,
                    message=f"Information for {normalized_path.name}",
                    data=info,
                    command_type=CommandType.GET_INFO
                )
            except Exception as e:
                return CommandResult(
                    success=False,
                    message=f"Failed to get info: {str(e)}",
                    command_type=CommandType.GET_INFO
                )
        else:
            # Get system info
            info = {
                "system": platform.system(),
                "platform": platform.platform(),
                "home": str(Path.home()),
                "cwd": os.getcwd(),
                "python_version": platform.python_version(),
            }
            
            return CommandResult(
                success=True,
                message="System information retrieved",
                data=info,
                command_type=CommandType.GET_INFO
            )
    
    async def _chat(self, params: Dict[str, Any]) -> CommandResult:
        """Handle general conversation/questions using AI"""
        question = params.get("question", "")
        
        try:
            # Use Ollama to generate a conversational response
            prompt = f"""You are LIA (Local Intelligent Agent), a helpful AI assistant. 
Answer the user's question in a friendly, conversational way. Keep your response concise but informative.

User's question: {question}

Your response:"""
            
            response = await self.ollama_service.generate_content(prompt, max_tokens=500)
            
            return CommandResult(
                success=True,
                message=response.strip(),
                data={"question": question},
                command_type=CommandType.CHAT
            )
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return CommandResult(
                success=False,
                message=f"I had trouble answering that. Error: {str(e)}",
                command_type=CommandType.CHAT
            )
    
    async def _help(self, params: Dict[str, Any]) -> CommandResult:
        """Show help and available commands"""
        try:
            help_text = """
🤖 **LIA (Local Intelligent Agent) - Help & Commands**

## 📁 **File Operations**
• **Open folder**: "Open Downloads", "Show Pictures folder"
• **List files**: "List all files", "Show PDF files in Documents"
• **Create file**: "Create notes.txt", "Make a new file called todo.md"
• **Read file**: "Read config.txt", "Show me the contents of script.sh"
• **Delete file**: "Delete old_file.txt", "Remove temporary files"

## 🔧 **System Commands**
• **System info**: "Show system information", "What's my uptime?"
• **Process management**: "Show running processes", "List all users"
• **Network**: "Ping google.com", "Show network connections"
• **Disk usage**: "Show disk space", "Check Downloads folder size"

## 💬 **Chat & Help**
• **General questions**: "What is Python?", "Explain machine learning"
• **Help**: "Show available commands", "What can you do?"
• **Mode switching**: Use sidebar to switch between Auto/Commands/Chat modes

## 🎯 **Available Safe Commands (100+)**

**File Operations**: ls, pwd, cd, mkdir, rmdir, touch, cat, head, tail, less, more, wc, sort, uniq, grep, find, locate, which, whereis, file, stat, du, df, chmod, chown, chgrp, ln, readlink

**Text Processing**: awk, sed, cut, paste, join, diff, cmp, comm, tr, expand, unexpand, fold, fmt, pr, column, nl, tac, rev, base64, hexdump, od

**System Info**: uname, hostname, whoami, id, groups, who, w, users, last, lastlog, uptime, date, cal, time, env, printenv, set, ps, top, htop, free, vmstat, iostat, sar, netstat, ss, lsof, fuser, lscpu, lsmem

**Network**: ping, traceroute, nslookup, dig, host, curl, wget, nc, telnet, ssh, scp, rsync, ifconfig, ip, route, arp, iptables, ufw

**Process Management**: kill, killall, pkill, pgrep, jobs, bg, fg, nohup, screen, tmux, at, crontab, systemctl, service, initctl

**Archive & Compression**: tar, gzip, gunzip, bzip2, bunzip2, xz, unxz, zip, unzip, 7z, rar, unrar, cpio, ar, zipinfo

**Package Management**: apt, apt-get, apt-cache, dpkg, yum, dnf, rpm, pacman, brew, pip, npm, yarn, gem, cargo, go, maven, gradle

**Development Tools**: git, svn, hg, make, cmake, gcc, g++, clang, python, python3, node, npm, yarn, java, javac, javadoc, mvn, gradle, docker, docker-compose, kubectl, helm, terraform, ansible

**Monitoring**: tail, journalctl, dmesg, syslog, logger, watch, strace, ltrace, tcpdump, wireshark, tcpflow, ngrep, iftop, iotop, nethogs

**Utilities**: man, info, help, type, alias, history, clear, reset, stty, tty, mesg, write, wall, talk, finger, whois, wget, curl, lynx, links, elinks, w3m, tree, exa, bat, fd, ripgrep

## 🔒 **Security Features**
• Commands are whitelisted for safety
• Dangerous operations are blocked
• Output is truncated for long results
• Timeout protection prevents hanging
• Safe working directory enforcement

## 🌍 **Multilingual Support**
I understand commands in multiple languages including English, Azerbaijani, and more!

**Try asking**: "What can you do?", "Show me system info", "List files in Downloads"
"""
            
            return CommandResult(
                success=True,
                message=help_text.strip(),
                data={"help_type": "general"},
                command_type=CommandType.HELP
            )
            
        except Exception as e:
            logger.error(f"Help error: {e}")
            return CommandResult(
                success=False,
                message=f"I had trouble showing help. Error: {str(e)}",
                command_type=CommandType.HELP
            )

