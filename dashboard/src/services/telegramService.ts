import api from './api';

export interface TelegramAuthData {
  phoneNumber: string;
}

export interface TelegramVerifyData {
  code: string;
}

const telegramService = {
  // Start Telegram authentication process
  startAuth: async (data: TelegramAuthData): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/telegram/auth', data);
    return response.data;
  },

  // Verify Telegram authentication code
  verifyCode: async (data: TelegramVerifyData): Promise<{ message: string; success: boolean }> => {
    const response = await api.post<{ message: string; success: boolean }>('/telegram/verify', data);
    return response.data;
  },

  // Disconnect Telegram account
  disconnect: async (): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/telegram/disconnect');
    return response.data;
  }
};

export default telegramService; 