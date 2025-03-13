import { useContext } from 'react';
import AuthContext from '../context/AuthContext';

// This hook is a simple re-export of the useAuth function from the AuthContext
// It's created as a separate file for better organization and to avoid circular dependencies
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default useAuth; 