/**
 * Toast Notification System
 * Simple, elegant toast notifications for user feedback
 */

class ToastManager {
  constructor() {
    this.container = null;
    this.toasts = [];
    this.init();
  }

  init() {
    if (typeof document === 'undefined') return;
    
    // Create container if it doesn't exist
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        pointer-events: none;
      `;
      document.body.appendChild(this.container);
    }
  }

  show(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const colors = {
      success: 'rgba(106, 158, 127, 0.95)',
      error: 'rgba(199, 124, 124, 0.95)',
      warning: 'rgba(255, 193, 7, 0.95)',
      info: 'rgba(68, 104, 130, 0.95)'
    };
    
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ⓘ'
    };
    
    toast.style.cssText = `
      background: ${colors[type] || colors.info};
      color: white;
      padding: 16px 24px;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(20px);
      font-size: 14px;
      font-weight: 500;
      min-width: 250px;
      max-width: 400px;
      pointer-events: all;
      transform: translateX(400px);
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      display: flex;
      align-items: center;
      gap: 12px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    `;
    
    toast.innerHTML = `
      <span style="font-size: 18px; flex-shrink: 0;">${icons[type] || icons.info}</span>
      <span style="flex: 1;">${message}</span>
    `;
    
    this.container.appendChild(toast);
    this.toasts.push(toast);
    
    // Animate in
    setTimeout(() => {
      toast.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto dismiss
    setTimeout(() => {
      this.dismiss(toast);
    }, duration);
    
    // Click to dismiss
    toast.addEventListener('click', () => this.dismiss(toast));
    
    return toast;
  }

  dismiss(toast) {
    toast.style.transform = 'translateX(400px)';
    toast.style.opacity = '0';
    
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      this.toasts = this.toasts.filter(t => t !== toast);
    }, 400);
  }

  success(message, duration) {
    return this.show(message, 'success', duration);
  }

  error(message, duration) {
    return this.show(message, 'error', duration);
  }

  warning(message, duration) {
    return this.show(message, 'warning', duration);
  }

  info(message, duration) {
    return this.show(message, 'info', duration);
  }

  clear() {
    this.toasts.forEach(toast => this.dismiss(toast));
  }
}

// Create singleton instance
const toast = new ToastManager();

export default toast;

