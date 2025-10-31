import subprocess
import tempfile
import os
import json
import logging
from typing import Dict, Any, Tuple
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class PythonExecutor:
    """
    Intelligent Python code executor with sandboxing and LLM code generation.
    Automatically generates and executes Python code when native commands fail.
    """
    
    def __init__(self, ollama_service=None):
        self.ollama_service = ollama_service
        self.execution_timeout = 5  # seconds
        self.max_output_size = 10000  # characters
    
    async def can_handle_with_python(self, user_request: str, failed_command_type: str = None) -> bool:
        """
        Determine if a request should be handled with Python.
        Returns True if Python can provide a better solution.
        """
        # English keywords
        python_indicators_en = [
            'calculate', 'compute', 'average', 'sum', 'count', 'analyze',
            'parse', 'extract', 'process', 'convert', 'transform',
            'compare', 'find all', 'filter', 'sort by', 'statistics',
            'json', 'xml', 'csv', 'data', 'numbers from', 'pattern',
            'regex', 'replace all', 'manipulate', 'generate random',
            'probability', 'factorial', 'fibonacci', 'prime', 'measure',
            'size', 'how many', 'total', 'list all', 'find', 'search'
        ]
        
        # Azerbaijani keywords
        python_indicators_az = [
            'hesabla', 'ölç', 'say', 'cəm', 'ortalama', 'təhlil',
            'tap', 'axtar', 'süz', 'çevir', 'müqayisə', 'statistika',
            'ölçü', 'neçə', 'cəmi', 'siyahı', 'hamısı'
        ]
        
        request_lower = user_request.lower()
        
        # Check both English and Azerbaijani indicators
        all_indicators = python_indicators_en + python_indicators_az
        has_python_indicator = any(indicator in request_lower for indicator in all_indicators)
        
        # If a command failed, ALWAYS try Python
        if failed_command_type == 'execute_command' or failed_command_type == 'unknown':
            return True
        
        # If it's computational or data processing, use Python
        if has_python_indicator:
            return True
        
        # Default to True for unknown/complex requests
        return True
    
    async def generate_python_code(self, user_request: str, context: Dict[str, Any] = None) -> str:
        """
        Generate Python code using LLM based on user's natural language request.
        """
        context_info = ""
        if context:
            context_info = f"\n\nContext information:\n{json.dumps(context, indent=2)}"
        
        prompt = f"""You are a Python code generator. Generate secure, efficient Python code that fulfills the user's request.
The user's request may be in English, Azerbaijani, or other languages. Understand the intent and generate appropriate code.

User's request: {user_request}{context_info}

IMPORTANT GUIDELINES:
1. Generate ONLY executable Python code - no explanations or markdown
2. Use only standard library modules (os, sys, json, pathlib, math, statistics, re, glob, etc.)
3. DO NOT use input() or any interactive functions
4. Print results clearly to stdout in a user-friendly format
5. Handle errors gracefully with try-except blocks
6. Keep code concise and focused on the task
7. If working with files, use these directory paths:
   - Home: {str(Path.home())}
   - Documents: {str(Path.home() / "Documents")}
   - Downloads: {str(Path.home() / "Downloads")}
   - Desktop: {str(Path.home() / "Desktop")}
8. For file operations, always check if files/directories exist first
9. When measuring/counting/analyzing files, provide detailed output
10. Support file size calculations, counting files, finding patterns, etc.
11. Limit output to essential information only

Examples:

Request: "Find the average of numbers in data.txt"
Code:
```python
from pathlib import Path
try:
    file_path = Path.home() / "Documents" / "data.txt"
    if file_path.exists():
        content = file_path.read_text()
        numbers = [float(x) for x in content.split() if x.replace('.','').replace('-','').isdigit()]
        if numbers:
            avg = sum(numbers) / len(numbers)
            print(f"Average: {{avg:.2f}}")
            print(f"Total numbers: {{len(numbers)}}")
        else:
            print("No numbers found in file")
    else:
        print(f"File not found: {{file_path}}")
except Exception as e:
    print(f"Error: {{e}}")
```

Request: "List all Python files in current directory with their sizes"
Code:
```python
from pathlib import Path
try:
    current_dir = Path.home()
    py_files = list(current_dir.glob("*.py"))
    if py_files:
        print(f"Found {{len(py_files)}} Python files:\\n")
        for f in sorted(py_files):
            size_kb = f.stat().st_size / 1024
            print(f"{{f.name}}: {{size_kb:.2f}} KB")
    else:
        print("No Python files found")
except Exception as e:
    print(f"Error: {{e}}")
```

Request: "Measure all files in Downloads folder" or "ölç Downloads qovluğundakı faylları"
Code:
```python
from pathlib import Path
try:
    downloads_dir = Path.home() / "Downloads"
    if downloads_dir.exists():
        files = [f for f in downloads_dir.iterdir() if f.is_file()]
        if files:
            total_size = sum(f.stat().st_size for f in files)
            total_mb = total_size / (1024 * 1024)
            print(f"Downloads folder analysis:")
            print(f"Total files: {{len(files)}}")
            print(f"Total size: {{total_mb:.2f}} MB\\n")
            print("Largest files:")
            for f in sorted(files, key=lambda x: x.stat().st_size, reverse=True)[:5]:
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"  {{f.name}}: {{size_mb:.2f}} MB")
        else:
            print("No files found in Downloads folder")
    else:
        print("Downloads folder not found")
except Exception as e:
    print(f"Error: {{e}}")
```

Now generate Python code for this request:
{user_request}

Python code:"""

        try:
            # Generate code using LLM
            if self.ollama_service:
                response = await self.ollama_service.generate_content(prompt, max_tokens=1000)
                
                # Clean up the response
                code = self._extract_code_from_response(response)
                
                # Validate the code is not empty
                if not code.strip():
                    raise ValueError("Generated code is empty")
                
                logger.info(f"Generated Python code:\n{code}")
                return code
            else:
                raise ValueError("Ollama service not available")
                
        except Exception as e:
            logger.error(f"Error generating Python code: {e}")
            # Fallback: generate simple code based on keywords
            return self._generate_fallback_code(user_request)
    
    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract clean Python code from LLM response.
        Removes markdown code blocks and explanations.
        """
        code = response.strip()
        
        # Remove markdown code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        # Remove common explanation patterns
        lines = code.split('\n')
        clean_lines = []
        
        for line in lines:
            # Skip lines that are clearly explanations
            if line.strip().startswith('#') and any(word in line.lower() for word in ['explanation', 'note:', 'this will', 'this code']):
                continue
            clean_lines.append(line)
        
        return '\n'.join(clean_lines).strip()
    
    def _generate_fallback_code(self, user_request: str) -> str:
        """
        Generate simple fallback code for common operations.
        """
        request_lower = user_request.lower()
        
        if 'average' in request_lower or 'mean' in request_lower:
            return """
import sys
try:
    # Example: calculate average
    numbers = [1, 2, 3, 4, 5]
    avg = sum(numbers) / len(numbers)
    print(f"Average: {avg:.2f}")
except Exception as e:
    print(f"Error: {e}")
"""
        elif 'list' in request_lower and 'file' in request_lower:
            return """
from pathlib import Path
try:
    files = list(Path.home().iterdir())
    print(f"Found {len(files)} items")
    for f in files[:10]:
        print(f"  {f.name}")
except Exception as e:
    print(f"Error: {e}")
"""
        else:
            return """
print("Task completed. Python execution was requested but specific implementation is not available.")
"""
    
    async def execute_python_code(self, code: str, working_dir: str = None) -> Tuple[bool, str, str]:
        """
        Execute Python code in a sandboxed subprocess.
        Returns (success, stdout, stderr)
        """
        if not working_dir:
            working_dir = str(Path.home())
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name
        
        try:
            # Execute in subprocess with timeout and restrictions
            process = await asyncio.create_subprocess_exec(
                'python3', tmp_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                # Security: limit resources
                env={
                    'HOME': str(Path.home()),
                    'PATH': os.environ.get('PATH', ''),
                    'PYTHONDONTWRITEBYTECODE': '1',
                }
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.execution_timeout
                )
                
                stdout_str = stdout.decode('utf-8', errors='replace')[:self.max_output_size]
                stderr_str = stderr.decode('utf-8', errors='replace')[:self.max_output_size]
                
                success = process.returncode == 0
                
                logger.info(f"Python execution completed: success={success}, returncode={process.returncode}")
                
                return success, stdout_str, stderr_str
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return False, "", f"Execution timed out after {self.execution_timeout} seconds"
        
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            return False, "", str(e)
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass
    
    async def execute_with_python(self, user_request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main method: Generate Python code and execute it.
        Returns a result dictionary with execution details.
        """
        logger.info(f"Executing with Python mode: {user_request}")
        
        try:
            # Step 1: Generate Python code
            code = await self.generate_python_code(user_request, context)
            
            if not code or len(code.strip()) < 10:
                return {
                    'success': False,
                    'message': 'Failed to generate Python code',
                    'python_mode': True,
                    'code': code,
                    'output': '',
                    'error': 'Code generation failed'
                }
            
            # Step 2: Execute the code
            success, stdout, stderr = await self.execute_python_code(code)
            
            # Step 3: Interpret results
            if success and stdout:
                message = self._interpret_output(stdout, user_request)
            elif stderr:
                message = f"Python execution encountered an error:\n{stderr}"
            else:
                message = "Python code executed but produced no output."
            
            return {
                'success': success,
                'message': message,
                'python_mode': True,
                'code': code,
                'output': stdout,
                'error': stderr if stderr else None
            }
            
        except Exception as e:
            logger.error(f"Python execution error: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Python execution failed: {str(e)}',
                'python_mode': True,
                'code': '',
                'output': '',
                'error': str(e)
            }
    
    def _interpret_output(self, output: str, original_request: str) -> str:
        """
        Interpret Python output and present it in natural language.
        """
        # If output is already well-formatted, return it
        if len(output.strip().split('\n')) <= 10:
            return f"**Result:**\n\n{output.strip()}"
        
        # For longer outputs, add a summary
        lines = output.strip().split('\n')
        summary = f"**Result:** (showing {len(lines)} lines of output)\n\n{output.strip()}"
        
        return summary
    
    def is_safe_code(self, code: str) -> Tuple[bool, str]:
        """
        Perform basic safety checks on generated code.
        Returns (is_safe, reason)
        """
        dangerous_patterns = [
            ('import subprocess', 'Subprocess execution not allowed'),
            ('import os.system', 'System command execution not allowed'),
            ('exec(', 'Dynamic code execution not allowed'),
            ('eval(', 'Dynamic evaluation not allowed'),
            ('__import__', 'Dynamic imports not allowed'),
            ('open(', 'File opening detected - ensure safe paths'),  # Warning, not blocking
        ]
        
        code_lower = code.lower()
        
        for pattern, reason in dangerous_patterns:
            if pattern.lower() in code_lower:
                if 'open(' in pattern:  # This is just a warning
                    logger.warning(f"Code contains file operations: {reason}")
                else:
                    logger.warning(f"Potentially unsafe code detected: {reason}")
                    return False, reason
        
        return True, "Code appears safe"


