/**
 * Copy Button Component
 * Provides easy copy-to-clipboard functionality
 */

import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import './CopyButton.css';

const CopyButton = ({ text, className = '' }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <button
      className={`copy-button ${copied ? 'copied' : ''} ${className}`}
      onClick={handleCopy}
      title={copied ? 'Copied!' : 'Copy to clipboard'}
    >
      {copied ? <Check size={16} /> : <Copy size={16} />}
      <span className="copy-button-text">{copied ? 'Copied!' : 'Copy'}</span>
    </button>
  );
};

export default CopyButton;

