/**
 * Markdown Renderer Component
 * Renders markdown with syntax highlighting
 */

import React, { useMemo } from 'react';
import './MarkdownRenderer.css';

const MarkdownRenderer = ({ content }) => {
  // Simple markdown parser (you can replace with a library like react-markdown)
  const parseMarkdown = (text) => {
    if (!text) return '';
    
    let html = text;
    
    // Code blocks with language
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
      const language = lang || 'text';
      const safe = escapeHtml(code.trim());
      return `<div class="code-block"><div class="code-meta">${language}</div><pre><code class="language-${language}">${safe}</code></pre></div>`;
    });
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Lists
    html = html.replace(/^\* (.+)$/gim, '<li>$1</li>');
    html = html.replace(/^- (.+)$/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br/>');
    
    return html;
  };
  
  const escapeHtml = (text) => {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  };
  
  const rendered = useMemo(() => parseMarkdown(content), [content]);
  return <div className="markdown-content" dangerouslySetInnerHTML={{ __html: rendered }} />;
};

export default MarkdownRenderer;

