'use client';

import { useState, useEffect } from 'react';
import { 
  MessageSquare, 
  Plus, 
  Trash2, 
  Clock, 
  ChevronLeft, 
  ChevronRight,
  Loader2,
  AlertCircle
} from 'lucide-react';

export interface ConversationSummary {
  id: string;
  application_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  preview?: string;
}

interface ChatHistoryPanelProps {
  applicationId: string;
  currentConversationId: string | null;
  onSelectConversation: (id: string | null) => void;
  onNewConversation: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export default function ChatHistoryPanel({
  applicationId,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  isCollapsed,
  onToggleCollapse,
}: ChatHistoryPanelProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Load conversations
  useEffect(() => {
    if (!applicationId) return;
    
    const loadConversations = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/applications/${applicationId}/conversations`);
        if (!response.ok) throw new Error('Failed to load conversations');
        const data = await response.json();
        setConversations(data.conversations || []);
      } catch (e) {
        console.error('Failed to load conversations:', e);
        setError('Failed to load history');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadConversations();
  }, [applicationId]);

  // Refresh conversations when a new one might be created
  const refreshConversations = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/applications/${applicationId}/conversations`);
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      }
    } catch (e) {
      console.error('Failed to refresh conversations:', e);
    }
  };

  // Expose refresh function
  useEffect(() => {
    (window as any).__refreshChatHistory = refreshConversations;
    return () => {
      delete (window as any).__refreshChatHistory;
    };
  }, [applicationId]);

  const handleDelete = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    if (deletingId) return;
    
    setDeletingId(conversationId);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${backendUrl}/api/applications/${applicationId}/conversations/${conversationId}`,
        { method: 'DELETE' }
      );
      
      if (response.ok) {
        setConversations(prev => prev.filter(c => c.id !== conversationId));
        if (currentConversationId === conversationId) {
          onSelectConversation(null);
        }
      }
    } catch (e) {
      console.error('Failed to delete conversation:', e);
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Collapsed state
  if (isCollapsed) {
    return (
      <div className="w-12 bg-slate-100 border-r border-slate-200 flex flex-col items-center py-3 gap-2">
        <button
          onClick={onToggleCollapse}
          className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
          title="Expand history"
        >
          <ChevronRight className="w-4 h-4 text-slate-600" />
        </button>
        <button
          onClick={onNewConversation}
          className="p-2 hover:bg-indigo-100 rounded-lg transition-colors"
          title="New conversation"
        >
          <Plus className="w-4 h-4 text-indigo-600" />
        </button>
        <div className="flex-1" />
        <div className="text-xs text-slate-400 transform -rotate-90 whitespace-nowrap">
          {conversations.length} chats
        </div>
      </div>
    );
  }

  return (
    <div className="w-56 bg-slate-50 border-r border-slate-200 flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-500" />
          <span className="text-sm font-medium text-slate-700">History</span>
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-1 hover:bg-slate-200 rounded transition-colors"
          title="Collapse"
        >
          <ChevronLeft className="w-4 h-4 text-slate-500" />
        </button>
      </div>

      {/* New Conversation Button */}
      <div className="p-2">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertCircle className="w-5 h-5 text-slate-400 mb-2" />
            <p className="text-xs text-slate-500">{error}</p>
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <MessageSquare className="w-8 h-8 text-slate-300 mb-2" />
            <p className="text-xs text-slate-500">No conversations yet</p>
            <p className="text-xs text-slate-400">Start a new chat!</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              className={`w-full text-left p-2 rounded-lg transition-colors group ${
                currentConversationId === conv.id
                  ? 'bg-indigo-100 border border-indigo-200'
                  : 'hover:bg-slate-100 border border-transparent'
              }`}
            >
              <div className="flex items-start justify-between gap-1">
                <div className="flex-1 min-w-0">
                  <p className={`text-xs font-medium truncate ${
                    currentConversationId === conv.id ? 'text-indigo-800' : 'text-slate-700'
                  }`}>
                    {conv.title}
                  </p>
                  {conv.preview && (
                    <p className="text-xs text-slate-500 truncate mt-0.5">
                      {conv.preview}
                    </p>
                  )}
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-400">
                      {formatDate(conv.updated_at)}
                    </span>
                    <span className="text-xs text-slate-400">
                      {conv.message_count} msgs
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDelete(e, conv.id)}
                  className={`p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity ${
                    deletingId === conv.id ? 'opacity-100' : ''
                  } hover:bg-rose-100`}
                  title="Delete"
                >
                  {deletingId === conv.id ? (
                    <Loader2 className="w-3 h-3 text-rose-500 animate-spin" />
                  ) : (
                    <Trash2 className="w-3 h-3 text-rose-500" />
                  )}
                </button>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
