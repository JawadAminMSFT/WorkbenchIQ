'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Send, MessageSquare, Bot, User, Loader2, Trash2, Minimize2 } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onOpen: () => void;
  applicationId: string;
}

const STORAGE_KEY_PREFIX = 'underwriting-chat-';

export default function ChatDrawer({
  isOpen,
  onClose,
  onOpen,
  applicationId,
}: ChatDrawerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  // Load chat history from localStorage
  useEffect(() => {
    if (isOpen && applicationId) {
      const storageKey = `${STORAGE_KEY_PREFIX}${applicationId}`;
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setMessages(parsed.map((m: any) => ({
            ...m,
            timestamp: new Date(m.timestamp),
          })));
        } catch (e) {
          console.error('Failed to load chat history:', e);
        }
      }
    }
  }, [isOpen, applicationId]);

  // Save chat history to localStorage
  useEffect(() => {
    if (applicationId && messages.length > 0) {
      const storageKey = `${STORAGE_KEY_PREFIX}${applicationId}`;
      localStorage.setItem(storageKey, JSON.stringify(messages));
    }
  }, [messages, applicationId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when drawer opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Build history for API (excluding timestamps)
      const history = messages.map(m => ({
        role: m.role,
        content: m.content,
      }));

      // Use AbortController for timeout (2 minutes for LLM responses)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000);

      // Call backend directly to avoid Next.js proxy timeout issues
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/applications/${applicationId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          history,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Chat failed: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, messages, applicationId]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearHistory = () => {
    const storageKey = `${STORAGE_KEY_PREFIX}${applicationId}`;
    localStorage.removeItem(storageKey);
    setMessages([]);
  };

  // Format message content with basic markdown support
  const formatContent = (content: string) => {
    // Handle code blocks
    const parts = content.split(/```(\w+)?\n([\s\S]*?)```/g);
    const elements: React.ReactNode[] = [];
    
    for (let i = 0; i < parts.length; i++) {
      if (i % 3 === 0) {
        // Regular text - handle inline formatting
        const text = parts[i];
        if (text) {
          // Handle policy IDs
          const withPolicies = text.replace(
            /\b([A-Z]+-[A-Z]+-\d+)\b/g,
            '<span class="font-mono text-xs bg-indigo-100 text-indigo-700 px-1 py-0.5 rounded">$1</span>'
          );
          // Handle bold
          const withBold = withPolicies.replace(
            /\*\*(.*?)\*\*/g,
            '<strong>$1</strong>'
          );
          elements.push(
            <span
              key={i}
              dangerouslySetInnerHTML={{ __html: withBold }}
            />
          );
        }
      } else if (i % 3 === 1) {
        // Language identifier - skip
        continue;
      } else {
        // Code block
        elements.push(
          <pre key={i} className="bg-slate-800 text-slate-100 p-3 rounded-lg text-xs overflow-x-auto my-2">
            <code>{parts[i]}</code>
          </pre>
        );
      }
    }
    
    return elements;
  };

  // Show floating button when closed
  if (!isOpen) {
    return (
      <button
        onClick={onOpen}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 hover:shadow-xl transition-all duration-200 group"
        title="Ask IQ - Chat with AI Assistant"
      >
        <MessageSquare className="w-5 h-5" />
        <span className="font-medium text-sm">Ask IQ</span>
        {messages.length > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-rose-500 text-white text-xs rounded-full flex items-center justify-center">
            {messages.length > 9 ? '9+' : messages.length}
          </span>
        )}
      </button>
    );
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-2xl z-50 flex flex-col"
        style={{ animation: 'slideIn 0.2s ease-out' }}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-900">
                Ask IQ
              </h2>
              <p className="text-xs text-slate-500">
                Ask about policies & this application
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {messages.length > 0 && (
              <button
                onClick={handleClearHistory}
                className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                title="Clear chat history"
              >
                <Trash2 className="w-4 h-4 text-slate-500" />
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <Bot className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p className="text-sm text-slate-500">
                Ask me anything about this application or underwriting policies.
              </p>
              <div className="mt-4 space-y-2">
                <p className="text-xs text-slate-400">Try asking:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {[
                    'What are the key risk factors?',
                    'Which policies apply here?',
                    'Should I approve this application?',
                  ].map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputValue(suggestion)}
                      className="text-xs px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-indigo-600" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-100 text-slate-800'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">
                    {msg.role === 'assistant' ? formatContent(msg.content) : msg.content}
                  </div>
                  <div className={`text-xs mt-1 ${
                    msg.role === 'user' ? 'text-indigo-200' : 'text-slate-400'
                  }`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-lg bg-slate-200 flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-slate-600" />
                  </div>
                )}
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="bg-slate-100 rounded-lg px-4 py-3">
                <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-slate-200 bg-white">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your question..."
              className="flex-1 resize-none rounded-lg border border-slate-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              rows={2}
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              className="self-end px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>

      <style jsx>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
      `}</style>
    </>
  );
}
