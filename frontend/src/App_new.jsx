import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Send, 
  Bot, 
  User, 
  Settings,
  Plus,
  MessageSquare,
  Home,
  Bell,
  Share2,
  HelpCircle,
  Paperclip,
  ChevronRight,
  X,
  Download,
  Smartphone,
  ChevronLeft,
  Trash2
} from 'lucide-react';
import './App_new.css';

// Dynamic API URL - will be set when component loads
let API_URL = 'http://localhost:8000'; // Default fallback

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [aiMode, setAiMode] = useState('local'); // 'local' or 'general'
  const [agentMode, setAgentMode] = useState('auto'); // 'auto', 'chat', 'command'
  const [currentModel, setCurrentModel] = useState('Llama 3');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showDownloadBanner, setShowDownloadBanner] = useState(true);
  const [showModelTypeMenu, setShowModelTypeMenu] = useState(false);
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [showAgentModeMenu, setShowAgentModeMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [availableModels, setAvailableModels] = useState({
    local_models: [],
    general_models: [],
    current_local: 'llama3',
    current_general: 'x-ai/grok-code-fast-1'
  });
  const [thinkingMode, setThinkingMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('lia_dark_mode');
    return saved ? JSON.parse(saved) : false;
  });
  // UI Customization State
  const [uiSettings, setUiSettings] = useState(() => {
    const saved = localStorage.getItem('lia_ui_settings');
    return saved ? JSON.parse(saved) : {
      primaryColor: '#6366f1',
      accentColor: '#8b5cf6',
      backgroundColor: '#f5f5f5',
      sidebarColor: '#ffffff',
      textColor: '#111827',
      messageBubbleColor: '#f3f4f6',
      fontFamily: 'system-ui',
      fontSize: '16px',
      borderRadius: '12px',
      glassEffect: true,
      glassIntensity: 0.3,
      animationSpeed: '15s'
    };
  });
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Save dark mode preference
  useEffect(() => {
    localStorage.setItem('lia_dark_mode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Apply UI customization settings
  useEffect(() => {
    localStorage.setItem('lia_ui_settings', JSON.stringify(uiSettings));
    const root = document.documentElement;
    root.style.setProperty('--primary-color', uiSettings.primaryColor);
    root.style.setProperty('--accent-color', uiSettings.accentColor);
    root.style.setProperty('--background-color', uiSettings.backgroundColor);
    root.style.setProperty('--sidebar-color', uiSettings.sidebarColor);
    root.style.setProperty('--text-color', uiSettings.textColor);
    root.style.setProperty('--message-bubble-color', uiSettings.messageBubbleColor);
    root.style.setProperty('--font-family', uiSettings.fontFamily);
    root.style.setProperty('--font-size', uiSettings.fontSize);
    root.style.setProperty('--border-radius', uiSettings.borderRadius);
    root.style.setProperty('--glass-effect', uiSettings.glassEffect ? '1' : '0');
    root.style.setProperty('--glass-intensity', uiSettings.glassIntensity);
    root.style.setProperty('--animation-speed', uiSettings.animationSpeed);
  }, [uiSettings]);

  // Check backend connection and load models on mount
  useEffect(() => {
    const initializeApp = async () => {
      // Electron environment check - get dynamic backend port
      if (window.electronAPI) {
        try {
          const backendPort = await window.electronAPI.getBackendPort();
          if (backendPort && backendPort !== 8000) {
            API_URL = `http://127.0.0.1:${backendPort}`;
            console.log(`Updated API URL to: ${API_URL}`);
          }
        } catch (error) {
          console.log('Could not get backend port, using default');
        }
      }
      
      checkConnection();
      loadAvailableModels();
      loadChatHistory();
    };
    
    initializeApp();
  }, []);

  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    if (chatHistory.length > 0) {
      localStorage.setItem('lia_chat_history', JSON.stringify(chatHistory));
    }
  }, [chatHistory]);

  // Save current chat messages
  useEffect(() => {
    if (currentChatId && messages.length > 0) {
      setChatHistory(prev => prev.map(chat => 
        chat.id === currentChatId 
          ? { ...chat, messages, updatedAt: new Date().toISOString() }
          : chat
      ));
    }
  }, [messages, currentChatId]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const checkConnection = async () => {
    try {
      await axios.get(`${API_URL}/health`);
      setConnectionStatus('connected');
    } catch (error) {
      setConnectionStatus('disconnected');
    }
  };

  const loadChatHistory = () => {
    const saved = localStorage.getItem('lia_chat_history');
    if (saved) {
      try {
        const history = JSON.parse(saved);
        setChatHistory(history);
      } catch (e) {
        console.error('Error loading chat history:', e);
      }
    }
  };

  const createNewChat = () => {
    const newChat = {
      id: Date.now(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    setChatHistory(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setMessages([]);
  };

  const switchToChat = (chatId) => {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat) {
      setCurrentChatId(chatId);
      setMessages(chat.messages);
    }
  };

  const deleteChat = (chatId) => {
    setChatHistory(prev => prev.filter(c => c.id !== chatId));
    if (currentChatId === chatId) {
      setCurrentChatId(null);
      setMessages([]);
    }
    localStorage.setItem('lia_chat_history', JSON.stringify(chatHistory.filter(c => c.id !== chatId)));
  };

  const getChatTitle = (chat) => {
    if (chat.messages.length > 0) {
      const firstUserMessage = chat.messages.find(m => m.role === 'user');
      if (firstUserMessage) {
        return firstUserMessage.content.slice(0, 40) + (firstUserMessage.content.length > 40 ? '...' : '');
      }
    }
    return 'New Chat';
  };

  const formatChatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const loadAvailableModels = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/models`);
      setAvailableModels(response.data);
      
      // Set current model name based on mode
      if (aiMode === 'local') {
        const localModel = response.data.local_models.find(m => m.id === response.data.current_local);
        if (localModel) setCurrentModel(localModel.name);
      } else {
        const generalModel = response.data.general_models.find(m => m.id === response.data.current_general);
        if (generalModel) setCurrentModel(generalModel.name);
      }
    } catch (error) {
      console.error('Error loading models:', error);
    }
  };

  const switchModel = async (mode, modelId) => {
    try {
      const response = await axios.post(`${API_URL}/api/models/switch`, {
        mode: mode,
        model_id: modelId
      });
      
      if (response.data.success) {
        // Update local state
        if (mode === 'local') {
          setAvailableModels(prev => ({ ...prev, current_local: modelId }));
          const model = availableModels.local_models.find(m => m.id === modelId);
          if (model) setCurrentModel(model.name);
        } else {
          setAvailableModels(prev => ({ ...prev, current_general: modelId }));
          const model = availableModels.general_models.find(m => m.id === modelId);
          if (model) setCurrentModel(model.name);
        }
        console.log(response.data.message);
      }
    } catch (error) {
      console.error('Error switching model:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');

    // Create new chat if none exists
    if (!currentChatId) {
      const newChat = {
        id: Date.now(),
        title: userMessage.slice(0, 40) + (userMessage.length > 40 ? '...' : ''),
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      setChatHistory(prev => [newChat, ...prev]);
      setCurrentChatId(newChat.id);
    }

    // Add user message to chat
    const newUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      if (useStreaming) {
        // Streaming with typewriter effect
        let tempAssistant = {
          role: 'assistant',
          content: '⏳ Processing...',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, tempAssistant]);

        let accumulatedContent = '';
        const response = await fetch(`${API_URL}/api/chat/stream/v2`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMessage, mode: aiMode, thinking_mode: thinkingMode })
        });

        if (!response.ok || !response.body) throw new Error(`Stream error: ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let thinkingContent = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          
          // Split by double newline for SSE format
          const events = buffer.split('\n\n');
          buffer = events.pop() || ''; // Keep incomplete event in buffer
          
          for (const event of events) {
            if (!event.trim()) continue;
            
            const lines = event.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const parsed = JSON.parse(line.slice(6));
                  
                  if (parsed.type === 'token') {
                    accumulatedContent += parsed.content;
                    setMessages(prev => {
                      const updated = [...prev];
                      const lastIdx = updated.length - 1;
                      const prefix = thinkingContent ? `🤔 *${thinkingContent}*\n\n` : '';
                      updated[lastIdx] = {
                        role: 'assistant',
                        content: prefix + accumulatedContent,
                        timestamp: new Date().toISOString()
                      };
                      return updated;
                    });
                  } else if (parsed.type === 'thinking') {
                    thinkingContent = parsed.content;
                    setMessages(prev => {
                      const updated = [...prev];
                      const lastIdx = updated.length - 1;
                      updated[lastIdx] = {
                        role: 'assistant',
                        content: `🤔 *${parsed.content}*\n\n${accumulatedContent}`,
                        timestamp: new Date().toISOString()
                      };
                      return updated;
                    });
                  } else if (parsed.type === 'result') {
                    setMessages(prev => {
                      const updated = [...prev];
                      const lastIdx = updated.length - 1;
                      updated[lastIdx] = {
                        role: 'assistant',
                        content: parsed.data.content,
                        timestamp: parsed.data.timestamp
                      };
                      return updated;
                    });
                  } else if (parsed.type === 'error') {
                    setMessages(prev => {
                      const updated = [...prev];
                      const lastIdx = updated.length - 1;
                      updated[lastIdx] = {
                        role: 'assistant',
                        content: `❌ ${parsed.message}`,
                        timestamp: new Date().toISOString()
                      };
                      return updated;
                    });
                  }
                } catch (e) {
                  console.error('Parse error:', e, 'Line:', line);
                }
              }
            }
          }
        }
        setConnectionStatus('connected');
      } else {
        // Regular non-streaming mode
        const response = await axios.post(`${API_URL}/api/chat`, {
          message: userMessage,
          mode: aiMode
        });
        setMessages(prev => [...prev, response.data]);
        setConnectionStatus('connected');
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || error.message || 'Failed to connect to backend'}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      setConnectionStatus('disconnected');
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleShare = () => {
    // Share functionality
    if (navigator.share) {
      navigator.share({
        title: 'LIA Chat',
        text: 'Check out my conversation with LIA!',
        url: window.location.href
      }).catch(err => console.log('Error sharing:', err));
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  const handleChangeModelType = () => {
    console.log('Change model type clicked! Current state:', showModelTypeMenu);
    setShowModelTypeMenu(!showModelTypeMenu);
    setShowAgentModeMenu(false);
    setShowModelSelector(false);
  };

  const handleAgentMode = () => {
    console.log('Agent mode clicked! Current state:', showAgentModeMenu);
    setShowAgentModeMenu(!showAgentModeMenu);
    setShowModelTypeMenu(false);
    setShowModelSelector(false);
  };

  const handleModeSwitch = (newMode) => {
    setAiMode(newMode);
    setShowModelTypeMenu(false);
    
    // Update current model display
    if (newMode === 'local') {
      const model = availableModels.local_models.find(m => m.id === availableModels.current_local);
      if (model) setCurrentModel(model.name);
    } else {
      const model = availableModels.general_models.find(m => m.id === availableModels.current_general);
      if (model) setCurrentModel(model.name);
    }
  };

  const handleAgentModeChange = (newMode) => {
    setAgentMode(newMode);
    setShowAgentModeMenu(false);
  };

  const handleFileAttach = () => {
    // File attachment functionality
    const input = document.createElement('input');
    input.type = 'file';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        console.log('File selected:', file.name);
        // Handle file upload here
      }
    };
    input.click();
  };

  return (
    <div className="app-new">
      {/* Sidebar */}
      <div className={`sidebar-new ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header-new">
          <div className="logo-new">
            <Bot size={24} />
            <span>LIA</span>
          </div>
          <button 
            className="new-chat-btn-new"
            onClick={createNewChat}
            title="New Chat"
          >
            <Plus size={18} />
          </button>
        </div>

        <div className="sidebar-section-new">
          <div className="sidebar-title-new">Chat History</div>
          <div className="chat-history-new">
            {chatHistory.length === 0 ? (
              <div className="history-empty-new">
                <MessageSquare size={32} opacity={0.3} />
                <p>No conversations yet</p>
              </div>
            ) : (
              chatHistory.map((chat) => (
                <div
                  key={chat.id}
                  className={`chat-history-item-new ${currentChatId === chat.id ? 'active' : ''}`}
                  onClick={() => switchToChat(chat.id)}
                >
                  <MessageSquare size={16} />
                  <div className="chat-info-new">
                    <div className="chat-title-new">{getChatTitle(chat)}</div>
                    <div className="chat-date-new">{formatChatDate(chat.updatedAt)}</div>
                  </div>
                  <button
                    className="delete-chat-btn-new"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteChat(chat.id);
                    }}
                    title="Delete chat"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="sidebar-footer-new">
          <button className="sidebar-icon-btn-new" onClick={() => setShowUserMenu(!showUserMenu)}>
            <User size={20} />
            <span>Profile</span>
          </button>
          {/* Removed duplicate Settings icon - available in top bar */}
          <button className="sidebar-icon-btn-new">
            <Bell size={20} />
            <span>Notifications</span>
          </button>
        </div>
      </div>

      {/* Sidebar Toggle Button */}
      <button 
        className="sidebar-toggle-btn-new"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      {/* Main Content */}
      <div className="main-new">
        {/* Top Navigation Bar */}
        <div className="topbar-new">
          <div className="breadcrumb-new">
            <span className="breadcrumb-home-new">
              <Home size={16} />
            </span>
            <ChevronRight size={16} className="breadcrumb-separator-new" />
            <span className="breadcrumb-item-new">
              {aiMode === 'local' ? 'Local mode' : 'General mode'}
            </span>
            <ChevronRight size={16} className="breadcrumb-separator-new" />
            <span className="breadcrumb-item-active-new">{currentModel}</span>
          </div>
          <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
            <button 
              className={`thinking-mode-btn-new ${thinkingMode ? 'active' : ''}`}
              onClick={() => setThinkingMode(!thinkingMode)}
              title="Toggle thinking mode"
            >
              🤔 {thinkingMode ? 'ON' : 'OFF'}
            </button>
            <button 
              className="dark-mode-btn-new" 
              onClick={() => setDarkMode(!darkMode)}
              title="Toggle dark mode"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
            <button 
              className="settings-btn-new" 
              onClick={() => setShowSettings(!showSettings)}
              title="Settings"
            >
              <Settings size={16} />
            </button>
            <button className="share-btn-new" onClick={handleShare}>
              <Share2 size={16} />
              Share
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="content-new">
          {messages.length === 0 ? (
            // Welcome Screen
            <div className="welcome-new">
              <h1 className="welcome-title-new">
                👋 Hello! I'm LIA your Local Intelligent Agent.
              </h1>
              
              <div className="action-buttons-new">
                <button 
                  className="action-card-new"
                  onClick={handleChangeModelType}
                >
                  <div className="action-card-icon-new">
                    <Bot size={20} />
                  </div>
                  <div className="action-card-content-new">
                    <div className="action-card-title-new">Change model type</div>
                  </div>
                  <Plus size={20} className="action-card-plus-new" />
                </button>

                <button 
                  className="action-card-new"
                  onClick={handleAgentMode}
                >
                  <div className="action-card-icon-new">
                    <Settings size={20} />
                  </div>
                  <div className="action-card-content-new">
                    <div className="action-card-title-new">Agent mode</div>
                  </div>
                  <Plus size={20} className="action-card-plus-new" />
                </button>
              </div>

              {/* Model Type Menu - Mode Switcher */}
              {showModelTypeMenu && (
                <>
                  <div className="dropdown-backdrop-new" onClick={() => setShowModelTypeMenu(false)}></div>
                  <div className="dropdown-menu-new">
                  <div className="dropdown-header-new">Select Mode</div>
                  <button 
                    className={`dropdown-item-new ${aiMode === 'local' ? 'active' : ''}`}
                    onClick={() => handleModeSwitch('local')}
                  >
                    <div className="dropdown-item-content-new">
                      <Home size={16} />
                      <div>
                        <div className="dropdown-item-title-new">Local Mode</div>
                        <div className="dropdown-item-desc-new">Uses Ollama (fast, private)</div>
                      </div>
                    </div>
                  </button>
                  <button 
                    className={`dropdown-item-new ${aiMode === 'general' ? 'active' : ''}`}
                    onClick={() => handleModeSwitch('general')}
                  >
                    <div className="dropdown-item-content-new">
                      <Bot size={16} />
                      <div>
                        <div className="dropdown-item-title-new">General Mode</div>
                        <div className="dropdown-item-desc-new">Uses OpenRouter (powerful, internet)</div>
                      </div>
                    </div>
                  </button>
                  
                  <div className="dropdown-divider-new"></div>
                  <div className="dropdown-header-new">
                    Select {aiMode === 'local' ? 'Local' : 'General'} Model
                  </div>
                  
                  {aiMode === 'local' ? (
                    // Local Models
                    availableModels.local_models.map((model) => (
                      <button
                        key={model.id}
                        className={`dropdown-item-new ${availableModels.current_local === model.id ? 'active' : ''}`}
                        onClick={() => {
                          switchModel('local', model.id);
                          setShowModelTypeMenu(false);
                        }}
                      >
                        <div className="dropdown-item-content-new">
                          <div>
                            <div className="dropdown-item-title-new">{model.name}</div>
                            <div className="dropdown-item-desc-new">Size: {model.size}</div>
                          </div>
                        </div>
                      </button>
                    ))
                  ) : (
                    // General Models
                    availableModels.general_models.map((model) => (
                      <button
                        key={model.id}
                        className={`dropdown-item-new ${availableModels.current_general === model.id ? 'active' : ''}`}
                        onClick={() => {
                          switchModel('general', model.id);
                          setShowModelTypeMenu(false);
                        }}
                      >
                        <div className="dropdown-item-content-new">
                          <div>
                            <div className="dropdown-item-title-new">{model.name}</div>
                            <div className="dropdown-item-desc-new">{model.provider}</div>
                          </div>
                        </div>
                      </button>
                    ))
                  )}
                </div>
                </>
              )}

              {/* Agent Mode Menu */}
              {showAgentModeMenu && (
                <>
                  <div className="dropdown-backdrop-new" onClick={() => setShowAgentModeMenu(false)}></div>
                  <div className="dropdown-menu-new">
                  <div className="dropdown-header-new">Select Agent Mode</div>
                  <button 
                    className={`dropdown-item-new ${agentMode === 'auto' ? 'active' : ''}`}
                    onClick={() => handleAgentModeChange('auto')}
                  >
                    <div className="dropdown-item-content-new">
                      <div>
                        <div className="dropdown-item-title-new">🤖 Auto Mode</div>
                        <div className="dropdown-item-desc-new">Automatically detects intent</div>
                      </div>
                    </div>
                  </button>
                  <button 
                    className={`dropdown-item-new ${agentMode === 'chat' ? 'active' : ''}`}
                    onClick={() => handleAgentModeChange('chat')}
                  >
                    <div className="dropdown-item-content-new">
                      <div>
                        <div className="dropdown-item-title-new">💬 Chat Mode</div>
                        <div className="dropdown-item-desc-new">Conversation only</div>
                      </div>
                    </div>
                  </button>
                  <button 
                    className={`dropdown-item-new ${agentMode === 'command' ? 'active' : ''}`}
                    onClick={() => handleAgentModeChange('command')}
                  >
                    <div className="dropdown-item-content-new">
                      <div>
                        <div className="dropdown-item-title-new">📁 Command Mode</div>
                        <div className="dropdown-item-desc-new">File operations only</div>
                      </div>
                    </div>
                  </button>
                </div>
                </>
              )}
            </div>
          ) : (
            // Messages Area
            <div className="messages-new">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`message-new ${message.role}`}
                >
                  <div className="message-avatar-new">
                    {message.role === 'user' ? (
                      <User size={20} />
                    ) : (
                      <Bot size={20} />
                    )}
                  </div>
                  <div className="message-content-new">
                    <div className="message-text-new">
                      {message.content}
                    </div>
                    
                    {/* Python Mode Indicator */}
                    {message.command_result?.python_mode && (
                      <div className="python-mode-indicator-new">
                        🐍 Command not supported natively. Switching to Python mode...
                      </div>
                    )}
                    
                    {/* Python Code Viewer */}
                    {message.command_result?.python_code && (
                      <details className="python-code-details-new">
                        <summary>🐍 View Generated Python Code</summary>
                        <pre className="python-code-new">{message.command_result.python_code}</pre>
                      </details>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message-new assistant">
                  <div className="message-avatar-new">
                    <Bot size={20} />
                  </div>
                  <div className="message-content-new">
                    <div className="loading-dots-new">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Input Area */}
          <div className="input-area-new">
            <form className="input-form-new" onSubmit={handleSubmit}>
              <button 
                type="button" 
                className="attach-btn-new"
                onClick={handleFileAttach}
                title="Attach file"
              >
                <Paperclip size={20} />
              </button>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask a follow up..."
                disabled={isLoading}
                className="input-field-new"
              />
              <button
                type="submit"
                disabled={isLoading || !inputValue.trim()}
                className="send-btn-new"
                title="Send message"
              >
                <Send size={20} />
              </button>
            </form>
          </div>
        </div>

        {/* Download Banner */}
        {showDownloadBanner && (
          <div className="download-banner-new">
            <div className="download-content-new">
              <Smartphone size={20} />
              <p>Download our app use LIA's full potential.</p>
            </div>
            <div className="download-actions-new">
              <button 
                className="dismiss-btn-new"
                onClick={() => setShowDownloadBanner(false)}
              >
                Dismiss
              </button>
              <button className="download-btn-new">
                Download App
              </button>
            </div>
            <button 
              className="close-banner-btn-new"
              onClick={() => setShowDownloadBanner(false)}
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Help Button */}
        <button className="help-btn-new" title="Help">
          <HelpCircle size={24} />
        </button>

        {/* Settings Panel */}
        {showSettings && (
          <div className="settings-overlay-new" onClick={() => setShowSettings(false)}>
            <div className="settings-panel-new" onClick={(e) => e.stopPropagation()}>
              <div className="settings-header-new">
                <h2>⚙️ Settings</h2>
                <button onClick={() => setShowSettings(false)}>✕</button>
              </div>
              <div className="settings-body-new">
                <div className="setting-group-new">
                  <h3>Performance</h3>
                  <label className="setting-item-new">
                    <span>Enable streaming (typewriter effect)</span>
                    <input 
                      type="checkbox" 
                      checked={useStreaming} 
                      onChange={(e) => setUseStreaming(e.target.checked)}
                    />
                  </label>
                  <label className="setting-item-new">
                    <span>Thinking mode (show AI reasoning)</span>
                    <input 
                      type="checkbox" 
                      checked={thinkingMode} 
                      onChange={(e) => setThinkingMode(e.target.checked)}
                    />
                  </label>
                  <label className="setting-item-new">
                    <span>Dark mode</span>
                    <input 
                      type="checkbox" 
                      checked={darkMode} 
                      onChange={(e) => setDarkMode(e.target.checked)}
                    />
                  </label>
                </div>
                <div className="setting-group-new">
                  <h3>Actions</h3>
                  <button className="action-btn-new" onClick={() => {
                    const json = JSON.stringify(messages, null, 2);
                    const blob = new Blob([json], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `lia-chat-${Date.now()}.json`;
                    a.click();
                    alert('Chat exported!');
                  }}>
                    📥 Export Chat (JSON)
                  </button>
                  <button className="action-btn-new" onClick={() => {
                    const text = messages.map(m => `${m.role}: ${m.content}`).join('\n\n');
                    const blob = new Blob([text], { type: 'text/plain' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `lia-chat-${Date.now()}.txt`;
                    a.click();
                    alert('Chat exported!');
                  }}>
                    📄 Export Chat (TXT)
                  </button>
                  <button className="action-btn-new danger-btn-new" onClick={() => {
                    if (window.confirm('Clear all chat history? This cannot be undone.')) {
                      setMessages([]);
                      alert('Chat cleared');
                    }
                  }}>
                    🗑️ Clear Chat
                  </button>
                </div>
                <div className="setting-group-new">
                  <h3>Search Messages</h3>
                  <input 
                    type="text" 
                    className="search-input-new"
                    placeholder="Search in messages..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  {searchQuery && (
                    <div className="search-results-new">
                      {messages.filter(m => 
                        m.content.toLowerCase().includes(searchQuery.toLowerCase())
                      ).map((msg, idx) => (
                        <div key={idx} className="search-result-item-new">
                          <strong>{msg.role}:</strong> {msg.content.substring(0, 100)}...
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* UI Customization */}
                <div className="setting-group-new">
                  <h3>🎨 UI Customization</h3>
                  
                  <div className="customization-section-new">
                    <h4>🎨 Colors</h4>
                    <label className="setting-item-new">
                      <span>Primary Color (Buttons)</span>
                      <input 
                        type="color" 
                        value={uiSettings.primaryColor} 
                        onChange={(e) => setUiSettings({...uiSettings, primaryColor: e.target.value})}
                      />
                    </label>
                    <label className="setting-item-new">
                      <span>Accent Color (Highlights)</span>
                      <input 
                        type="color" 
                        value={uiSettings.accentColor} 
                        onChange={(e) => setUiSettings({...uiSettings, accentColor: e.target.value})}
                      />
                    </label>
                    <label className="setting-item-new">
                      <span>Background Color (Arxa fon)</span>
                      <input 
                        type="color" 
                        value={uiSettings.backgroundColor} 
                        onChange={(e) => setUiSettings({...uiSettings, backgroundColor: e.target.value})}
                      />
                    </label>
                    <label className="setting-item-new">
                      <span>Sidebar Color</span>
                      <input 
                        type="color" 
                        value={uiSettings.sidebarColor} 
                        onChange={(e) => setUiSettings({...uiSettings, sidebarColor: e.target.value})}
                      />
                    </label>
                    <label className="setting-item-new">
                      <span>Text Color (Yazı rəngi)</span>
                      <input 
                        type="color" 
                        value={uiSettings.textColor} 
                        onChange={(e) => setUiSettings({...uiSettings, textColor: e.target.value})}
                      />
                    </label>
                    <label className="setting-item-new">
                      <span>Message Bubble Color</span>
                      <input 
                        type="color" 
                        value={uiSettings.messageBubbleColor} 
                        onChange={(e) => setUiSettings({...uiSettings, messageBubbleColor: e.target.value})}
                      />
                    </label>
                  </div>
                  
                  <div className="customization-section-new">
                    <h4>📝 Typography</h4>
                    <label className="setting-item-new">
                      <span>Font Family (Şrift)</span>
                      <select 
                        value={uiSettings.fontFamily} 
                        onChange={(e) => setUiSettings({...uiSettings, fontFamily: e.target.value})}
                        className="select-input-new"
                      >
                        <option value="system-ui">System UI</option>
                        <option value="'Segoe UI', sans-serif">Segoe UI</option>
                        <option value="'Roboto', sans-serif">Roboto</option>
                        <option value="'Inter', sans-serif">Inter</option>
                        <option value="'Poppins', sans-serif">Poppins</option>
                        <option value="'Open Sans', sans-serif">Open Sans</option>
                        <option value="'Lato', sans-serif">Lato</option>
                        <option value="monospace">Monospace</option>
                        <option value="'Comic Sans MS', cursive">Comic Sans (Fun)</option>
                      </select>
                    </label>
                    <label className="setting-item-new">
                      <span>Font Size (Şrift ölçüsü)</span>
                      <select 
                        value={uiSettings.fontSize} 
                        onChange={(e) => setUiSettings({...uiSettings, fontSize: e.target.value})}
                        className="select-input-new"
                      >
                        <option value="12px">Extra Small (12px)</option>
                        <option value="14px">Small (14px)</option>
                        <option value="16px">Medium (16px)</option>
                        <option value="18px">Large (18px)</option>
                        <option value="20px">Extra Large (20px)</option>
                        <option value="22px">Huge (22px)</option>
                      </select>
                    </label>
                  </div>

                  <div className="customization-section-new">
                    <h4>⭕ Shapes & Effects</h4>
                    <label className="setting-item-new">
                      <span>Border Radius (Künc dairəliyi)</span>
                      <select 
                        value={uiSettings.borderRadius} 
                        onChange={(e) => setUiSettings({...uiSettings, borderRadius: e.target.value})}
                        className="select-input-new"
                      >
                        <option value="0px">Square (0px)</option>
                        <option value="4px">Sharp (4px)</option>
                        <option value="8px">Slightly Rounded (8px)</option>
                        <option value="12px">Rounded (12px)</option>
                        <option value="16px">Very Rounded (16px)</option>
                        <option value="24px">Pill (24px)</option>
                        <option value="50%">Circle (50%)</option>
                      </select>
                    </label>
                    <label className="setting-item-new">
                      <span>🌟 Liquid Glass Effect</span>
                      <input 
                        type="checkbox" 
                        checked={uiSettings.glassEffect} 
                        onChange={(e) => setUiSettings({...uiSettings, glassEffect: e.target.checked})}
                      />
                    </label>
                    {uiSettings.glassEffect && (
                      <>
                        <label className="setting-item-new">
                          <span>Glass Intensity (Intensivlik)</span>
                          <input 
                            type="range" 
                            min="0" 
                            max="1" 
                            step="0.1"
                            value={uiSettings.glassIntensity} 
                            onChange={(e) => setUiSettings({...uiSettings, glassIntensity: parseFloat(e.target.value)})}
                            className="range-input-new"
                          />
                          <span className="range-value-new">{(uiSettings.glassIntensity * 100).toFixed(0)}%</span>
                        </label>
                        <label className="setting-item-new">
                          <span>Animation Speed (Animasiya sürəti)</span>
                          <select 
                            value={uiSettings.animationSpeed} 
                            onChange={(e) => setUiSettings({...uiSettings, animationSpeed: e.target.value})}
                            className="select-input-new"
                          >
                            <option value="30s">Slow (Yavaş)</option>
                            <option value="15s">Normal</option>
                            <option value="8s">Fast (Sürətli)</option>
                            <option value="5s">Very Fast</option>
                          </select>
                        </label>
                      </>
                    )}
                  </div>

                  <div className="customization-section-new">
                    <h4>🎭 Quick Themes (Hazır mövzular)</h4>
                    <div className="theme-presets-new">
                      <button 
                        className="theme-preset-btn-new"
                        onClick={() => setUiSettings({
                          ...uiSettings,
                          primaryColor: '#6366f1',
                          accentColor: '#8b5cf6',
                          backgroundColor: '#f5f5f5',
                          sidebarColor: '#ffffff',
                          textColor: '#111827',
                          messageBubbleColor: '#f3f4f6'
                        })}
                      >
                        🔵 Default
                      </button>
                      <button 
                        className="theme-preset-btn-new"
                        onClick={() => setUiSettings({
                          ...uiSettings,
                          primaryColor: '#ec4899',
                          accentColor: '#f43f5e',
                          backgroundColor: '#fce7f3',
                          sidebarColor: '#fff1f2',
                          textColor: '#881337',
                          messageBubbleColor: '#fce7f3'
                        })}
                      >
                        💖 Pink Dream
                      </button>
                      <button 
                        className="theme-preset-btn-new"
                        onClick={() => setUiSettings({
                          ...uiSettings,
                          primaryColor: '#10b981',
                          accentColor: '#14b8a6',
                          backgroundColor: '#ecfdf5',
                          sidebarColor: '#f0fdf4',
                          textColor: '#065f46',
                          messageBubbleColor: '#d1fae5'
                        })}
                      >
                        🌿 Nature Green
                      </button>
                      <button 
                        className="theme-preset-btn-new"
                        onClick={() => setUiSettings({
                          ...uiSettings,
                          primaryColor: '#f59e0b',
                          accentColor: '#fb923c',
                          backgroundColor: '#fffbeb',
                          sidebarColor: '#fef3c7',
                          textColor: '#78350f',
                          messageBubbleColor: '#fef3c7'
                        })}
                      >
                        🌅 Sunset Orange
                      </button>
                      <button 
                        className="theme-preset-btn-new"
                        onClick={() => setUiSettings({
                          ...uiSettings,
                          primaryColor: '#3b82f6',
                          accentColor: '#06b6d4',
                          backgroundColor: '#eff6ff',
                          sidebarColor: '#f0f9ff',
                          textColor: '#1e3a8a',
                          messageBubbleColor: '#dbeafe'
                        })}
                      >
                        🌊 Ocean Blue
                      </button>
                      <button 
                        className="theme-preset-btn-new"
                        onClick={() => setUiSettings({
                          ...uiSettings,
                          primaryColor: '#8b5cf6',
                          accentColor: '#a855f7',
                          backgroundColor: '#faf5ff',
                          sidebarColor: '#f5f3ff',
                          textColor: '#581c87',
                          messageBubbleColor: '#e9d5ff'
                        })}
                      >
                        🔮 Purple Magic
                      </button>
                    </div>
                  </div>
                  <div className="customization-actions-new">
                    <button 
                      className="action-btn-new reset-btn-new"
                      onClick={() => {
                        const defaultSettings = {
                          primaryColor: '#6366f1',
                          accentColor: '#8b5cf6',
                          backgroundColor: '#f5f5f5',
                          sidebarColor: '#ffffff',
                          textColor: '#111827',
                          messageBubbleColor: '#f3f4f6',
                          fontFamily: 'system-ui',
                          fontSize: '16px',
                          borderRadius: '12px',
                          glassEffect: true,
                          glassIntensity: 0.3,
                          animationSpeed: '15s'
                        };
                        setUiSettings(defaultSettings);
                      }}
                    >
                      🔄 Reset to Default (Standart)
                    </button>
                    <button 
                      className="action-btn-new export-btn-new"
                      onClick={() => {
                        const json = JSON.stringify(uiSettings, null, 2);
                        const blob = new Blob([json], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `lia-theme-${Date.now()}.json`;
                        a.click();
                        alert('Theme exported! (Mövzu ixrac edildi!)');
                      }}
                    >
                      💾 Export Theme (İxrac et)
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

