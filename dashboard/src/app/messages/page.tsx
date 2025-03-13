'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { SendMessageForm } from "@/components/messages/SendMessageForm";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useMessages } from "@/hooks/useMessages";
import { Message } from "@/services/messageService";
import { MessageSquare } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function MessagesPage() {
  const { messages, loading, error, totalMessages, currentPage, totalPages, getMessages } = useMessages();
  const [currentMessages, setCurrentMessages] = useState<Message[]>([]);

  useEffect(() => {
    getMessages({ page: 1, limit: 10 });
  }, []);

  useEffect(() => {
    if (messages) {
      setCurrentMessages(messages);
    }
  }, [messages]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${date.toLocaleTimeString()} - ${date.toLocaleDateString()}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'text-green-500';
      case 'sent':
        return 'text-blue-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-yellow-500';
    }
  };

  const handlePageChange = (page: number) => {
    getMessages({ page, limit: 10 });
  };

  return (
    <ProtectedRoute>
      <DashboardLayout title="Messages">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <SendMessageForm />
          </div>
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Message History</CardTitle>
                <CardDescription>
                  View your recent messages and their status
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center h-[300px]">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
                  </div>
                ) : currentMessages.length > 0 ? (
                  <div className="space-y-4">
                    {currentMessages.map((message) => (
                      <div key={message.id} className="flex items-center gap-4 p-3 border rounded-md">
                        <div className="rounded-full h-10 w-10 bg-primary/10 flex items-center justify-center">
                          <MessageSquare className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex justify-between">
                            <p className="text-sm font-medium">To: {message.recipient}</p>
                            <span className={`text-xs font-medium ${getStatusColor(message.status)}`}>
                              {message.status.charAt(0).toUpperCase() + message.status.slice(1)}
                            </span>
                          </div>
                          <p className="text-sm">{message.content}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(message.createdAt)}
                          </p>
                        </div>
                      </div>
                    ))}

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex justify-center mt-4 space-x-2">
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                          <button
                            key={page}
                            onClick={() => handlePageChange(page)}
                            className={`px-3 py-1 rounded-md ${
                              currentPage === page
                                ? 'bg-primary text-white'
                                : 'bg-gray-100 hover:bg-gray-200'
                            }`}
                          >
                            {page}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-[300px] text-center">
                    <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No messages found</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Send your first message using the form on the left
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
} 