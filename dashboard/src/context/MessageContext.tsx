import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import messageService, { 
  Message, 
  SendMessageData, 
  MessageStats, 
  MessageFilters,
  PaginatedMessages
} from '../services/messageService';
import { useAuth } from './AuthContext';

interface MessageContextType {
  messages: Message[];
  stats: MessageStats | null;
  loading: boolean;
  error: string | null;
  totalMessages: number;
  currentPage: number;
  totalPages: number;
  limit: number;
  sendMessage: (messageData: SendMessageData) => Promise<Message>;
  getMessages: (filters?: MessageFilters) => Promise<void>;
  getMessageStats: (filters?: { startDate?: string; endDate?: string }) => Promise<void>;
  getMessage: (id: string) => Promise<Message>;
  clearError: () => void;
}

const defaultStats: MessageStats = {
  total: 0,
  sent: 0,
  delivered: 0,
  failed: 0,
  pending: 0
};

const MessageContext = createContext<MessageContextType | undefined>(undefined);

export const useMessages = () => {
  const context = useContext(MessageContext);
  if (context === undefined) {
    throw new Error('useMessages must be used within a MessageProvider');
  }
  return context;
};

interface MessageProviderProps {
  children: ReactNode;
}

export const MessageProvider: React.FC<MessageProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [stats, setStats] = useState<MessageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalMessages, setTotalMessages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [limit, setLimit] = useState(10);
  
  const { isAuthenticated } = useAuth();

  // Fetch initial messages and stats when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      getMessages();
      getMessageStats();
    }
  }, [isAuthenticated]);

  const getMessages = async (filters: MessageFilters = {}) => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await messageService.getMessages({
        ...filters,
        page: filters.page || currentPage,
        limit: filters.limit || limit
      });
      
      setMessages(response.messages);
      setTotalMessages(response.total);
      setCurrentPage(response.page);
      setTotalPages(response.totalPages);
      setLimit(response.limit);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (messageData: SendMessageData): Promise<Message> => {
    setLoading(true);
    setError(null);
    try {
      const newMessage = await messageService.sendMessage(messageData);
      
      // Refresh messages and stats after sending
      getMessages();
      getMessageStats();
      
      return newMessage;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to send message');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getMessage = async (id: string): Promise<Message> => {
    setLoading(true);
    setError(null);
    try {
      return await messageService.getMessage(id);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to get message');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getMessageStats = async (filters: { startDate?: string; endDate?: string } = {}) => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    try {
      const messageStats = await messageService.getMessageStats(filters);
      setStats(messageStats);
    } catch (err: any) {
      console.error('Error fetching message stats:', err);
      // Don't set error for stats to avoid disrupting the UI
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    messages,
    stats,
    loading,
    error,
    totalMessages,
    currentPage,
    totalPages,
    limit,
    sendMessage,
    getMessages,
    getMessageStats,
    getMessage,
    clearError
  };

  return <MessageContext.Provider value={value}>{children}</MessageContext.Provider>;
};

export default MessageContext; 