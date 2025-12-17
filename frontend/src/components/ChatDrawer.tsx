'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Send, MessageSquare, Bot, User, Loader2, Trash2 } from 'lucide-react';
import { StructuredContentRenderer } from './chat/ChatCards';
import ChatHistoryPanel from './chat/ChatHistoryPanel';

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

export default function ChatDrawer({
  isOpen,
  onClose,
  onOpen,
  applicationId,
}: ChatDrawerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversationTitle, setConversationTitle] = useState<string>('New Chat');
  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  // Reset state when application changes
  useEffect(() => {
    setMessages([]);
    setConversationId(null);
    setConversationTitle('New Chat');
  }, [applicationId]);

  // Load a specific conversation
  const loadConversation = useCallback(async (convId: string | null) => {
    if (!convId) {
      // Start new conversation
      setMessages([]);
      setConversationId(null);
      setConversationTitle('New Chat');
      return;
    }

    setIsLoadingConversation(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${backendUrl}/api/applications/${applicationId}/conversations/${convId}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setMessages(
          (data.messages || []).map((m: any) => ({
            ...m,
            timestamp: new Date(m.timestamp),
          }))
        );
        setConversationId(data.id);
        setConversationTitle(data.title || 'Conversation');
      }
    } catch (e) {
      console.error('Failed to load conversation:', e);
    } finally {
      setIsLoadingConversation(false);
    }
  }, [applicationId]);

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
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000);

      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${backendUrl}/api/applications/${applicationId}/conversations`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage.content,
            conversation_id: conversationId,
          }),
          signal: controller.signal,
        }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Chat failed: ${response.status}`);
      }

      const data = await response.json();

      // Update conversation ID if this was a new conversation
      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id);
        setConversationTitle(data.title || 'New Chat');
        // Refresh the history panel
        if ((window as any).__refreshChatHistory) {
          (window as any).__refreshChatHistory();
        }
      }

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
  }, [inputValue, isLoading, applicationId, conversationId]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setConversationTitle('New Chat');
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const handleSelectConversation = (id: string | null) => {
    loadConversation(id);
  };

  return (
    <>
      {/* Floating Button - visible when drawer is closed */}
      <button
        onClick={onOpen}
        className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 hover:shadow-xl transition-all duration-300 group ${
          isOpen ? 'opacity-0 pointer-events-none translate-x-4' : 'opacity-100 translate-x-0'
        }`}
        title="Ask IQ - Chat with AI Assistant"
      >
        <MessageSquare className="w-5 h-5" />
        <span className="font-medium text-sm">Ask IQ</span>
      </button>

      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/20 z-40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className={`fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-2xl z-50 flex transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* History Panel */}
        <ChatHistoryPanel
          applicationId={applicationId}
          currentConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          isCollapsed={historyCollapsed}
          onToggleCollapse={() => setHistoryCollapsed(!historyCollapsed)}
        />

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  {conversationTitle}
                </h2>
                <p className="text-xs text-slate-500">
                  {conversationId ? `${messages.length} messages` : 'Start a new conversation'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {isLoadingConversation ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
              </div>
            ) : messages.length === 0 ? (
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
                    className={`max-w-[85%] rounded-lg px-4 py-2 ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-100 text-slate-800'
                    }`}
                  >
                    <div className="text-sm">
                      {msg.role === 'assistant' ? (
                        <StructuredContentRenderer content={msg.content} />
                      ) : (
                        <span className="whitespace-pre-wrap">{msg.content}</span>
                      )}
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
      </div>
    </>
  );
}
