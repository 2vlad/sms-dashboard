import React, { useEffect, useState } from 'react';
import { Layout } from '../../components/layout';
import { useAuth } from '../../context/AuthContext';
import messageService, { Message, MessageStats } from '../../services/messageService';
import useApi from '../../hooks/useApi';

const Dashboard = () => {
  const { user } = useAuth();
  const [recentMessages, setRecentMessages] = useState<Message[]>([]);
  
  const { 
    data: stats, 
    loading: statsLoading, 
    error: statsError,
    execute: fetchStats
  } = useApi<MessageStats>(() => messageService.getMessageStats());
  
  const { 
    loading: messagesLoading, 
    error: messagesError,
    execute: fetchMessages
  } = useApi<{ messages: Message[], total: number }>(
    () => messageService.getMessages(1, 5),
    {
      onSuccess: (data) => {
        setRecentMessages(data.messages);
      }
    }
  );

  useEffect(() => {
    fetchStats();
    fetchMessages();
  }, []);

  const loading = statsLoading || messagesLoading;
  const error = statsError || messagesError;

  return (
    <Layout title="Dashboard | SMS Dashboard">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user?.name || 'User'}
          </p>
        </div>

        {error && (
          <div className="bg-destructive/10 text-destructive p-4 rounded-md">
            Error loading dashboard data. Please try again.
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
            <h3 className="text-sm font-medium text-muted-foreground">Total Messages</h3>
            <p className="text-2xl font-bold mt-1">
              {loading ? '...' : stats?.total || 0}
            </p>
          </div>
          
          <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
            <h3 className="text-sm font-medium text-muted-foreground">Sent</h3>
            <p className="text-2xl font-bold mt-1 text-green-600 dark:text-green-400">
              {loading ? '...' : stats?.sent || 0}
            </p>
          </div>
          
          <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
            <h3 className="text-sm font-medium text-muted-foreground">Failed</h3>
            <p className="text-2xl font-bold mt-1 text-destructive">
              {loading ? '...' : stats?.failed || 0}
            </p>
          </div>
          
          <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
            <h3 className="text-sm font-medium text-muted-foreground">Pending</h3>
            <p className="text-2xl font-bold mt-1 text-amber-600 dark:text-amber-400">
              {loading ? '...' : stats?.pending || 0}
            </p>
          </div>
        </div>

        {/* Recent Messages */}
        <div className="bg-card rounded-lg border border-border shadow-sm">
          <div className="p-4 border-b border-border">
            <h2 className="text-lg font-medium">Recent Messages</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <p className="text-muted-foreground">Loading messages...</p>
            </div>
          ) : recentMessages.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-muted/50">
                    <th className="px-4 py-2 text-left text-sm font-medium">Recipient</th>
                    <th className="px-4 py-2 text-left text-sm font-medium">Content</th>
                    <th className="px-4 py-2 text-left text-sm font-medium">Status</th>
                    <th className="px-4 py-2 text-left text-sm font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {recentMessages.map((message) => (
                    <tr key={message.id} className="border-t border-border">
                      <td className="px-4 py-3 text-sm">{message.phoneNumber}</td>
                      <td className="px-4 py-3 text-sm">
                        {message.content.length > 50
                          ? `${message.content.substring(0, 50)}...`
                          : message.content}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            message.status === 'sent'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : message.status === 'failed'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              : 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
                          }`}
                        >
                          {message.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {new Date(message.createdAt).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-muted-foreground">No messages found</p>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard; 