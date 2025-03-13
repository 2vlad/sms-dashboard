import api from './api';

export interface Settings {
  id: string;
  userId: string;
  theme: 'light' | 'dark' | 'system';
  notifications: boolean;
  smsNotifications: boolean;
  emailNotifications: boolean;
  language: string;
  timezone: string;
  createdAt: string;
  updatedAt: string;
}

export interface UpdateSettingsData {
  theme?: 'light' | 'dark' | 'system';
  notifications?: boolean;
  smsNotifications?: boolean;
  emailNotifications?: boolean;
  language?: string;
  timezone?: string;
}

const settingService = {
  // Get user settings
  getSettings: async (): Promise<Settings> => {
    const response = await api.get<Settings>('/settings');
    return response.data;
  },

  // Update user settings
  updateSettings: async (settingsData: UpdateSettingsData): Promise<Settings> => {
    const response = await api.put<Settings>('/settings', settingsData);
    return response.data;
  }
};

export default settingService; 