import api from './api';

export interface Settings {
  id: string;
  userId: string;
  theme: 'light' | 'dark' | 'system';
  notificationsEnabled: boolean;
  emailNotifications: boolean;
  smsLowBalanceAlert: boolean;
  lowBalanceThreshold: number;
  defaultCountryCode: string;
  createdAt: string;
  updatedAt: string;
}

const settingsService = {
  // Get user settings
  getSettings: async (): Promise<Settings> => {
    const response = await api.get<Settings>('/settings');
    return response.data;
  },

  // Update user settings
  updateSettings: async (settingsData: Partial<Settings>): Promise<Settings> => {
    const response = await api.put<Settings>('/settings', settingsData);
    return response.data;
  }
};

export default settingsService; 