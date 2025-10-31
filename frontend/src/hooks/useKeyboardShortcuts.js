/**
 * Keyboard Shortcuts Hook
 * Provides easy-to-use keyboard shortcuts for the app
 */

import { useEffect } from 'react';

const useKeyboardShortcuts = (callbacks) => {
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Ctrl/Cmd + K - Focus search/command input
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        callbacks.onFocusInput?.();
      }
      
      // Ctrl/Cmd + N - New chat
      if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
        event.preventDefault();
        callbacks.onNewChat?.();
      }
      
      // Ctrl/Cmd + / - Toggle sidebar
      if ((event.ctrlKey || event.metaKey) && event.key === '/') {
        event.preventDefault();
        callbacks.onToggleSidebar?.();
      }
      
      // Ctrl/Cmd + B - Toggle sidebar (alternative)
      if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
        event.preventDefault();
        callbacks.onToggleSidebar?.();
      }
      
      // Ctrl/Cmd + L - Clear chat
      if ((event.ctrlKey || event.metaKey) && event.key === 'l') {
        event.preventDefault();
        callbacks.onClearChat?.();
      }
      
      // Ctrl/Cmd + , - Open settings
      if ((event.ctrlKey || event.metaKey) && event.key === ',') {
        event.preventDefault();
        callbacks.onOpenSettings?.();
      }
      
      // Escape - Close modals/dropdowns
      if (event.key === 'Escape') {
        callbacks.onEscape?.();
      }
      
      // Ctrl/Cmd + 1-9 - Switch to chat number
      if ((event.ctrlKey || event.metaKey) && /^[1-9]$/.test(event.key)) {
        event.preventDefault();
        const chatIndex = parseInt(event.key) - 1;
        callbacks.onSwitchChat?.(chatIndex);
      }
      
      // Ctrl/Cmd + Shift + C - Copy last response
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'C') {
        event.preventDefault();
        callbacks.onCopyLastResponse?.();
      }
      
      // Ctrl/Cmd + Shift + D - Toggle dark mode
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'D') {
        event.preventDefault();
        callbacks.onToggleTheme?.();
      }

      // Ctrl/Cmd + Shift + P - Open command palette
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && (event.key === 'P' || event.key === 'p')) {
        event.preventDefault();
        callbacks.onOpenPalette?.();
      }
      
      // Alt + Up/Down - Navigate chat history
      if (event.altKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
        event.preventDefault();
        callbacks.onNavigateHistory?.(event.key === 'ArrowUp' ? 'up' : 'down');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [callbacks]);
};

export default useKeyboardShortcuts;

