import api from './api';

export interface TelegramAuthData {
  phoneNumber: string;
}

export interface TelegramVerifyData {
  code: string;
}

export interface TelegramResponse {
  message: string;
  success: boolean;
}

const telegramService = {
  // Start Telegram authentication process
  startAuth: async (data: TelegramAuthData): Promise<TelegramResponse> => {
    const response = await api.post<TelegramResponse>('/telegram/auth', data);
    return response.data;
  },

  // Verify Telegram code
  verifyCode: async (data: TelegramVerifyData): Promise<TelegramResponse> => {
    const response = await api.post<TelegramResponse>('/telegram/verify', data);
    return response.data;
  },

  // Disconnect Telegram account
  disconnect: async (): Promise<TelegramResponse> => {
    const response = await api.post<TelegramResponse>('/telegram/disconnect');
    return response.data;
  }
};

export default telegramService; 