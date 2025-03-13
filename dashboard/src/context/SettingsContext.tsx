import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import settingsService, { Settings } from '../services/settingsService';
import { useAuth } from './AuthContext';

interface SettingsContextType {
  settings: Settings | null;
  loading: boolean;
  error: string | null;
  updateSettings: (settingsData: Partial<Settings>) => Promise<void>;
  setTheme: (theme: 'light' | 'dark' | 'system') => Promise<void>;
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
  const { user } = useAuth();

  // Fetch settings when user changes
  useEffect(() => {
    const fetchSettings = async () => {
      if (!user) {
        setSettings(null);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const userSettings = await settingsService.getSettings();
        setSettings(userSettings);
      } catch (err: any) {
        console.error('Failed to fetch settings:', err);
        setError(err.response?.data?.message || 'Failed to load settings.');
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, [user]);

  // Apply theme from settings
  useEffect(() => {
    if (settings) {
      applyTheme(settings.theme);
    }
  }, [settings]);

  // Helper function to apply theme
  const applyTheme = (theme: 'light' | 'dark' | 'system') => {
    const root = window.document.documentElement;
    
    // Remove existing theme classes
    root.classList.remove('light', 'dark');
    
    // Apply new theme
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
    
    // Store the theme preference
    localStorage.setItem('theme', theme);
  };

  // Update settings
  const updateSettings = async (settingsData: Partial<Settings>) => {
    setLoading(true);
    setError(null);
    try {
      const updatedSettings = await settingsService.updateSettings(settingsData);
      setSettings(updatedSettings);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update settings.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Set theme shorthand
  const setTheme = async (theme: 'light' | 'dark' | 'system') => {
    if (settings) {
      await updateSettings({ theme });
    }
  };

  const value = {
    settings,
    loading,
    error,
    updateSettings,
    setTheme,
  };

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export default SettingsContext; 