/**
 * Command History Manager
 * Stores and retrieves command history with localStorage persistence
 */

class CommandHistory {
  constructor(maxSize = 100) {
    this.maxSize = maxSize;
    this.storageKey = 'lia_command_history';
    this.currentIndex = -1;
    this.tempInput = '';
    this.load();
  }

  load() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      this.history = stored ? JSON.parse(stored) : [];
      this.currentIndex = -1;
    } catch (error) {
      console.error('Error loading command history:', error);
      this.history = [];
    }
  }

  save() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.history));
    } catch (error) {
      console.error('Error saving command history:', error);
    }
  }

  add(command) {
    if (!command || !command.trim()) return;
    
    // Remove duplicate if exists
    this.history = this.history.filter(item => item !== command);
    
    // Add to beginning
    this.history.unshift(command);
    
    // Trim to max size
    if (this.history.length > this.maxSize) {
      this.history = this.history.slice(0, this.maxSize);
    }
    
    this.currentIndex = -1;
    this.save();
  }

  getPrevious(currentInput = '') {
    if (this.history.length === 0) return null;
    
    if (this.currentIndex === -1) {
      this.tempInput = currentInput;
      this.currentIndex = 0;
    } else if (this.currentIndex < this.history.length - 1) {
      this.currentIndex++;
    }
    
    return this.history[this.currentIndex];
  }

  getNext() {
    if (this.currentIndex === -1) return null;
    
    this.currentIndex--;
    
    if (this.currentIndex === -1) {
      return this.tempInput;
    }
    
    return this.history[this.currentIndex];
  }

  reset() {
    this.currentIndex = -1;
    this.tempInput = '';
  }

  getAll() {
    return [...this.history];
  }

  clear() {
    this.history = [];
    this.currentIndex = -1;
    this.tempInput = '';
    this.save();
  }

  search(query) {
    if (!query) return this.getAll();
    return this.history.filter(cmd => 
      cmd.toLowerCase().includes(query.toLowerCase())
    );
  }
}

export default new CommandHistory();

