import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import settingService, { Settings, UpdateSettingsData } from '../services/settingService';
import { useAuth } from './AuthContext';

interface SettingsContextType {
  settings: Settings | null;
  loading: boolean;
  error: string | null;
  updateSettings: (settingsData: UpdateSettingsData) => Promise<void>;
  clearError: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

interface SettingsProviderProps {
  children: ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  // Fetch settings when user is authenticated
  useEffect(() => {
    const fetchSettings = async () => {
      if (!isAuthenticated) {
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const userSettings = await settingService.getSettings();
        setSettings(userSettings);
      } catch (err: any) {
        console.error('Error fetching settings:', err);
        setError(err.response?.data?.message || 'Failed to load settings');
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, [isAuthenticated]);

  const updateSettings = async (settingsData: UpdateSettingsData) => {
    setLoading(true);
    setError(null);
    try {
      const updatedSettings = await settingService.updateSettings(settingsData);
      setSettings(updatedSettings);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update settings');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    settings,
    loading,
    error,
    updateSettings,
    clearError
  };

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export default SettingsContext; 