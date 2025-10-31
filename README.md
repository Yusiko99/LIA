# LIA - Local Intelligent Agent

A powerful local AI assistant that runs entirely offline on your computer using Ollama as the LLM backend. LIA understands natural language commands and can safely execute file operations, folder management, and more.

![LIA](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![React](https://img.shields.io/badge/React-18.2-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)

## 🌟 Features

- **100% Offline** - Runs entirely on your local machine
- **Natural Language Interface** - Communicate in plain English
- **Multi-Interface** - Web UI, CLI, and REST API
- **Secure Command Execution** - Safe, sandboxed file operations
- **Modern UI** - Beautiful dark theme React interface
- **Powered by Ollama** - Uses local LLMs (llama3) for intelligent parsing
- **File Operations** - Open files/folders, list, create, delete, copy, move, rename
- **File Management** - Copy, move, rename files and directories
- **AI Content Generation** - Generate file contents using LLM
- **Safe Shell Commands** - Execute whitelisted system commands
- **CLI Interface** - Use from terminal with natural language
- **🐍 Python Mode** - Intelligent Python code generation and execution for complex tasks
  - Automatic fallback when native commands can't handle requests
  - Handles calculations, data analysis, pattern extraction, and more
  - Sandboxed execution with security safeguards
  - Subtle UI indication with code visibility

## 📋 Prerequisites

Before running LIA, ensure you have:

1. **Python 3.8 or higher** (Python 3.11-3.13 recommended)
   ```bash
   python3 --version
   ```

2. **Node.js 16 or higher**
   ```bash
   node --version
   ```

3. **Ollama installed and running**
   
   Install Ollama from: https://ollama.ai
   
   Then pull a model (e.g., llama3):
   ```bash
   ollama pull llama3
   ```
   
   Start Ollama server:
   ```bash
   ollama serve
   ```

## 🚀 Quick Start

### 0. One-Command Setup (installs Ollama if missing)

```bash
git clone 
cd /home/$USERNAMEHERE$/LIA
chmod +x setup.sh
./setup.sh
./run.sh
```

What this does:
- Checks and installs Ollama if it's missing, and starts the server
- Guides you to select a local model, including `hf.co/Yusiko/LIA` (Llama 3.1 finetuned for LIA)
- Optionally pre-downloads the chosen model so the first run is smooth

AZ (Qurulum – bir əmrlə):
- Ollama yoxlanır/quraşdırılır və işə salınır
- Yerli model seçimi üçün bələdçi açılır (`hf.co/Yusiko/LIA` daxil olmaqla)
- Seçilmiş model əvvəlcədən endirilə bilər ki, ilk işə salınmada gecikmə olmasın

### 1. Clone or Navigate to Project

```bash
cd LIA
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Backend (Optional)

Create a `.env` file in the `backend` directory:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
HOST=0.0.0.0
PORT=8000
ALLOWED_DIRECTORIES=/home/$USERNAMEHERE$
```

### 4. Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install
```

### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 6. Open Browser

Navigate to: http://localhost:5173

---

### Add to PATH (Optional)

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="/home/$USERNAMEHERE$/LIA:$PATH"

# Then use from anywhere
cd ~/Documents
lia "List all PDF files"
```

📖 **Full CLI Guide**: See [CLI_GUIDE.md](CLI_GUIDE.md) for complete documentation.

---

## 💬 Example Commands

### Open Files & Folders
```
"Open the Pictures folder"
"Open image.jpg"
"Open document.pdf"
```

### List & Search Files
```
"List all PDF files in Downloads"
"Show me all images in Pictures"
"Search for Python files"
```

### Create & Edit Files
```
"Create a file named notes.txt"
"Create report.txt and write 3 pages about AI"
"Write 'Hello World' to test.txt"
```

### File Management
```
"Delete old.txt"
"Copy file.txt to backup.txt"
"Move image.jpg to Pictures"
"Rename old.txt to new.txt"
```

### Information & System
```
"Get info about document.pdf"
"Show me my system information"
"Run ls"
"Run date"
```

### 🐍 Python Mode (Computational Tasks)
```
"Calculate the factorial of 10"
"Find the average of numbers in data.txt"
"Count how many times 'error' appears in system.log"
"Extract all email addresses from contacts.txt"
"List all files larger than 10MB in Downloads"
```
*Python Mode automatically activates for complex tasks that native commands can't handle!*

## 🏗️ Architecture

### Backend (Python/FastAPI)

```
backend/
├── main.py              # FastAPI application entry point
├── lia_cli.py           # Command-line interface
├── config.py            # Configuration management
├── models.py            # Pydantic models and schemas
├── ollama_service.py    # Ollama LLM integration
├── command_executor.py  # Safe command execution
├── python_executor.py   # 🐍 Python Mode: Code generation & execution
└── requirements.txt     # Python dependencies
```

**Key Components:**

- **FastAPI Server** - REST API for frontend communication
- **Ollama Service** - Natural language parsing and content generation
- **Command Executor** - Secure, sandboxed command execution
- **🐍 Python Executor** - Intelligent Python code generation and execution for complex tasks
- **CLI Interface** - Terminal-based interaction
- **Path Validation** - Ensures operations stay within allowed directories

**Supported Operations:**
- Open files/folders (`open_file`, `open_folder`)
- List & search files (`list_files`, `search_files`)
- Create, read, write, delete files
- Copy, move, rename files (`copy_file`, `move_file`, `rename_file`)
- Get file/system info (`get_info`)
- Execute safe shell commands (`execute_command`)

### Frontend (React/Vite)

```
frontend/
├── src/
│   ├── App.jsx         # Main application component
│   ├── App.css         # Component styles
│   ├── index.css       # Global styles
│   └── main.jsx        # React entry point
├── index.html
├── package.json
└── vite.config.js
```

**Key Features:**

- Modern chat interface
- Real-time command execution feedback
- File list visualization
- Connection status monitoring
- Dark theme with smooth animations

## 🔒 Security

LIA implements multiple security layers:

1. **Path Validation** - All file paths are validated and normalized
2. **Directory Whitelisting** - Operations restricted to allowed directories
3. **Command Sandboxing** - Only safe, predefined operations allowed
4. **🐍 Python Sandboxing** - Python code runs in isolated subprocess with timeout (5s) and restricted environment
5. **Code Safety Checks** - Validates generated Python code for dangerous patterns
6. **Local Execution** - Everything runs on your machine, no data sent externally

## 🛠️ Configuration

### Backend Configuration

Edit `backend/.env`:

- `OLLAMA_HOST` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model to use (default: llama3). You can also set `hf.co/Yusiko/LIA`.
- `PORT` - Backend server port (default: 8000)
- `ALLOWED_DIRECTORIES` - Base directory for file operations

### Frontend Configuration

Edit `frontend/src/App.jsx`:

- `API_URL` - Backend API URL (default: http://localhost:8000)

## 📊 API Endpoints

### Health Check
```
GET /health
```

### Process Chat Message
```
POST /api/chat
Body: { "message": "your command here" }
```

### Generate Content
```
POST /api/generate
Body: { "message": "content prompt" }
```

## 🐛 Troubleshooting

### Backend Won't Start

1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Verify Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Connection Error

1. Ensure backend is running on port 8000
2. Check CORS settings in `backend/main.py`
3. Verify frontend API_URL matches backend address

### Ollama Not Responding

1. Start Ollama:
   ```bash
   ollama serve
   ```

2. Pull required model:
   ```bash
   ollama pull llama2
   ```

## 🔧 Development

### Adding New Commands

1. Add command type to `models.py`:
   ```python
   class CommandType(str, Enum):
       YOUR_COMMAND = "your_command"
   ```

2. Implement handler in `command_executor.py`:
   ```python
   async def _your_command(self, params: Dict[str, Any]) -> CommandResult:
       # Implementation
   ```

3. Update LLM prompt in `ollama_service.py`

## 📝 License

MIT License - Feel free to use and modify as needed.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 🎯 Roadmap

Future enhancements:

- [ ] WebSocket for real-time updates
- [ ] Streaming LLM responses
- [ ] File preview in UI
- [ ] Multi-model support (switch models on-the-fly)
- [ ] Voice input/output
- [ ] Command history persistence
- [ ] Scheduled tasks
- [ ] Plugin system
- [ ] Docker deployment
- [ ] Mobile app

## 💡 Tips

1. **Model Selection** - Larger models (like llama2:13b) provide better understanding but require more resources
2. **Performance** - First command may be slower as Ollama loads the model
3. **Safety** - Always review what LIA will do before confirming sensitive operations
4. **Custom Paths** - Use absolute paths for operations outside your home directory

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review Ollama documentation: https://ollama.ai/docs
- Check FastAPI docs: https://fastapi.tiangolo.com
- You can contact with me

---

Built with ❤️ using Python, React, and Ollama

