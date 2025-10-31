#!/bin/bash

# LIA Setup Script
# This script helps configure LIA with your OpenRouter API key and models

echo "🤖 Welcome to LIA (Local Intelligent Agent) Setup!"
echo "=================================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    touch .env
fi

# Function to update or add environment variable
update_env() {
    local key=$1
    local value=$2
    
    if grep -q "^${key}=" .env; then
        # Update existing key
        sed -i "s/^${key}=.*/${key}=${value}/" .env
    else
        # Add new key
        echo "${key}=${value}" >> .env
    fi
}

# Ensure Ollama is installed and running
echo "🧰 Checking Ollama installation..."
if ! command -v ollama >/dev/null 2>&1; then
    echo "⚠️  Ollama not found."
    read -p "Install Ollama now? [Y/n]: " INSTALL_OLLAMA
    INSTALL_OLLAMA=${INSTALL_OLLAMA:-Y}
    if [[ "$INSTALL_OLLAMA" =~ ^[Yy]$ ]]; then
        echo "⬇️  Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh || {
            echo "❌ Failed to install Ollama. Please install manually from https://ollama.com"; exit 1;
        }
    else
        echo "❌ Ollama is required for Local mode. Exiting setup."; exit 1;
    fi
fi

echo "🔌 Ensuring Ollama server is running..."
if ! curl -sS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    # Try to start in background
    (nohup ollama serve >/dev/null 2>&1 &)
    # wait a bit
    sleep 2
fi

if curl -sS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama is running."
else
    echo "⚠️  Unable to verify Ollama server on 127.0.0.1:11434. You may need to run 'ollama serve' manually."
fi

# Ask for OpenRouter API Key
echo "🔑 OpenRouter API Configuration"
echo "==============================="
echo "To use General mode, you need an OpenRouter API key."
echo "Get your API key from: https://openrouter.ai/keys"
echo ""

read -p "Enter your OpenRouter API key (or press Enter to skip): " OPENROUTER_API_KEY

if [ ! -z "$OPENROUTER_API_KEY" ]; then
    update_env "OPENROUTER_API_KEY" "$OPENROUTER_API_KEY"
    echo "✅ OpenRouter API key saved!"
    
    # Ask for preferred model
    echo ""
    echo "🤖 Available OpenRouter Models:"
    echo "1. x-ai/grok-code-fast-1 (Current default)"
    echo "2. deepseek/deepseek-v3.2-exp (New model)"
    echo "3. Custom model name"
    echo ""
    
    read -p "Choose your preferred model (1-3): " MODEL_CHOICE
    
    case $MODEL_CHOICE in
        1)
            update_env "OPENROUTER_MODEL" "x-ai/grok-code-fast-1"
            echo "✅ Using x-ai/grok-code-fast-1"
            ;;
        2)
            update_env "OPENROUTER_MODEL" "deepseek/deepseek-v3.2-exp"
            echo "✅ Using deepseek/deepseek-v3.2-exp"
            ;;
        3)
            read -p "Enter custom model name: " CUSTOM_MODEL
            update_env "OPENROUTER_MODEL" "$CUSTOM_MODEL"
            echo "✅ Using custom model: $CUSTOM_MODEL"
            ;;
        *)
            update_env "OPENROUTER_MODEL" "x-ai/grok-code-fast-1"
            echo "✅ Using default model: x-ai/grok-code-fast-1"
            ;;
    esac
else
    echo "⏭️  Skipping OpenRouter configuration"
fi

# Ask about Ollama models
echo ""
echo "🏠 Ollama Local Models Configuration"
echo "===================================="
echo "Available local models:"
echo "1. llama3 (Current default)"
echo "2. hf.co/Yusiko/LIA (Finetuned LIA on Llama 3.1)"
echo "3. gemma2:12b"
echo "4. Custom model name"
echo ""

read -p "Choose your preferred local model (1-4): " OLLAMA_CHOICE

case $OLLAMA_CHOICE in
    1)
        update_env "OLLAMA_MODEL" "llama3"
        echo "✅ Using llama3"
        ;;
    2)
        update_env "OLLAMA_MODEL" "hf.co/Yusiko/LIA"
        echo "✅ Using hf.co/Yusiko/LIA"
        ;;
    3)
        update_env "OLLAMA_MODEL" "gemma2:12b"
        echo "✅ Using gemma2:12b"
        ;;
    4)
        read -p "Enter custom Ollama model name: " CUSTOM_OLLAMA_MODEL
        update_env "OLLAMA_MODEL" "$CUSTOM_OLLAMA_MODEL"
        echo "✅ Using custom Ollama model: $CUSTOM_OLLAMA_MODEL"
        ;;
    *)
        update_env "OLLAMA_MODEL" "llama3"
        echo "✅ Using default Ollama model: llama3"
        ;;
esac

# Set other default configurations
update_env "OLLAMA_HOST" "http://localhost:11434"
update_env "HOST" "0.0.0.0"
update_env "PORT" "8000"

echo ""
echo "📦 Model availability"
echo "====================="
CURR_MODEL=$(grep '^OLLAMA_MODEL=' .env | cut -d'=' -f2)
read -p "Download/start selected model now ($CURR_MODEL)? [Y/n]: " PULL_NOW
PULL_NOW=${PULL_NOW:-Y}
if [[ "$PULL_NOW" =~ ^[Yy]$ ]]; then
    echo "⬇️  Starting model once to trigger download (this may take time)..."
    # 'ollama run' both pulls (if needed) and tests the model, then exits when user sends EOF.
    # For headless: run promptless for a moment then terminate
    timeout 10s ollama run "$CURR_MODEL" >/dev/null 2>&1 || true
    echo "✅ Model checked: $CURR_MODEL"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Configuration Summary:"
echo "• OpenRouter API Key: ${OPENROUTER_API_KEY:+✅ Set}${OPENROUTER_API_KEY:-❌ Not set}"
echo "• OpenRouter Model: $(grep '^OPENROUTER_MODEL=' .env | cut -d'=' -f2)"
echo "• Ollama Model: $(grep '^OLLAMA_MODEL=' .env | cut -d'=' -f2)"
echo "• Ollama Host: $(grep '^OLLAMA_HOST=' .env | cut -d'=' -f2)"
echo ""
echo "🚀 Next Steps:"
echo "1. Make sure Ollama is running: ollama serve"
echo "2. Pull your chosen model: ollama pull $(grep '^OLLAMA_MODEL=' .env | cut -d'=' -f2)"
echo "3. Start the backend: cd backend && python main.py"
echo "4. Start the frontend: cd frontend && npm run dev"
echo ""
echo "💡 You can change these settings anytime by editing the .env file"
echo "   or running this setup script again."
echo ""