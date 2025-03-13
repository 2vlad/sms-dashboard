import api from './api';

export interface Message {
  id: string;
  userId: string;
  phoneNumber: string;
  content: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed';
  createdAt: string;
  updatedAt: string;
}

export interface SendMessageData {
  phoneNumber: string;
  content: string;
}

export interface MessageStats {
  total: number;
  sent: number;
  delivered: number;
  failed: number;
  pending: number;
  dailyCounts: {
    date: string;
    count: number;
  }[];
}

const messageService = {
  // Get all messages with optional pagination
  getMessages: async (page = 1, limit = 10): Promise<{ messages: Message[], total: number }> => {
    const response = await api.get<{ messages: Message[], total: number }>('/messages', {
      params: { page, limit }
    });
    return response.data;
  },

  // Get a single message by ID
  getMessage: async (id: string): Promise<Message> => {
    const response = await api.get<Message>(`/messages/${id}`);
    return response.data;
  },

  // Send a new SMS message
  sendMessage: async (messageData: SendMessageData): Promise<Message> => {
    const response = await api.post<Message>('/messages', messageData);
    return response.data;
  },

  // Get message statistics
  getMessageStats: async (): Promise<MessageStats> => {
    const response = await api.get<MessageStats>('/messages/stats');
    return response.data;
  }
};

export default messageService; 