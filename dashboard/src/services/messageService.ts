import api from './api';

export interface Message {
  id: string;
  userId: string;
  recipient: string;
  content: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed';
  createdAt: string;
  updatedAt: string;
}

export interface SendMessageData {
  recipient: string;
  content: string;
}

export interface MessageStats {
  total: number;
  sent: number;
  delivered: number;
  failed: number;
  pending: number;
}

export interface MessageFilters {
  status?: string;
  startDate?: string;
  endDate?: string;
  recipient?: string;
  page?: number;
  limit?: number;
}

export interface PaginatedMessages {
  messages: Message[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

const messageService = {
  // Get all messages with optional filtering
  getMessages: async (filters: MessageFilters = {}): Promise<PaginatedMessages> => {
    const response = await api.get<PaginatedMessages>('/messages', { params: filters });
    return response.data;
  },

  // Send a new message
  sendMessage: async (messageData: SendMessageData): Promise<Message> => {
    const response = await api.post<Message>('/messages', messageData);
    return response.data;
  },

  // Get a specific message by ID
  getMessage: async (id: string): Promise<Message> => {
    const response = await api.get<Message>(`/messages/${id}`);
    return response.data;
  },

  // Get message statistics
  getMessageStats: async (filters: { startDate?: string; endDate?: string } = {}): Promise<MessageStats> => {
    const response = await api.get<MessageStats>('/messages/stats', { params: filters });
    return response.data;
  }
};

export default messageService; 