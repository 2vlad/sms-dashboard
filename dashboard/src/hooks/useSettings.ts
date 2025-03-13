import { useContext } from 'react';
import SettingsContext from '../context/SettingsContext';

// This hook is a simple re-export of the useSettings function from the SettingsContext
// It's created as a separate file for better organization and to avoid circular dependencies
export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

export default useSettings; 