import { useContext } from 'react';
import MessageContext from '../context/MessageContext';

// This hook is a simple re-export of the useMessages function from the MessageContext
// It's created as a separate file for better organization and to avoid circular dependencies
export const useMessages = () => {
  const context = useContext(MessageContext);
  if (context === undefined) {
    throw new Error('useMessages must be used within a MessageProvider');
  }
  return context;
};

export default useMessages; 