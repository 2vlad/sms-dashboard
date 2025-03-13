import type { AppProps } from 'next/app';
import { AuthProvider } from '../context/AuthContext';
import { SettingsProvider } from '../context/SettingsContext';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <SettingsProvider>
        <Component {...pageProps} />
      </SettingsProvider>
    </AuthProvider>
  );
} 