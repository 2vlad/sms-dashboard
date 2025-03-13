import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { MessageSquare, CheckCircle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

// Sample data for messages
const messages = [
  {
    id: 1,
    recipient: "+1234567890",
    content: "Your verification code is 123456",
    status: "Delivered",
    timestamp: "2023-05-15T10:30:00",
  },
  {
    id: 2,
    recipient: "+0987654321",
    content: "Your appointment is confirmed for tomorrow at 2 PM",
    status: "Delivered",
    timestamp: "2023-05-15T11:15:00",
  },
  {
    id: 3,
    recipient: "+1122334455",
    content: "Your order #12345 has been shipped",
    status: "Failed",
    timestamp: "2023-05-15T12:00:00",
  },
  {
    id: 4,
    recipient: "+5566778899",
    content: "Your payment of $50.00 has been processed",
    status: "Delivered",
    timestamp: "2023-05-15T13:45:00",
  },
  {
    id: 5,
    recipient: "+9988776655",
    content: "Your account password has been reset",
    status: "Pending",
    timestamp: "2023-05-15T14:30:00",
  },
  {
    id: 6,
    recipient: "+1234509876",
    content: "Thank you for your purchase!",
    status: "Delivered",
    timestamp: "2023-05-15T15:15:00",
  },
  {
    id: 7,
    recipient: "+6655443322",
    content: "Your flight has been delayed by 1 hour",
    status: "Failed",
    timestamp: "2023-05-15T16:00:00",
  },
  {
    id: 8,
    recipient: "+1212343456",
    content: "Your subscription will renew in 3 days",
    status: "Delivered",
    timestamp: "2023-05-15T16:45:00",
  },
];

export default function MessagesPage() {
  return (
    <DashboardLayout title="Messages">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Recent Messages</h2>
        <Button>
          <MessageSquare className="mr-2 h-4 w-4" />
          Send New Message
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Message History</CardTitle>
          <CardDescription>
            View and manage all your SMS messages
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Recipient</TableHead>
                <TableHead>Content</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {messages.map((message) => (
                <TableRow key={message.id}>
                  <TableCell>{message.id}</TableCell>
                  <TableCell>{message.recipient}</TableCell>
                  <TableCell className="max-w-[300px] truncate">
                    {message.content}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      {message.status === "Delivered" ? (
                        <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                      ) : message.status === "Failed" ? (
                        <XCircle className="mr-2 h-4 w-4 text-red-500" />
                      ) : (
                        <MessageSquare className="mr-2 h-4 w-4 text-yellow-500" />
                      )}
                      {message.status}
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(message.timestamp).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
} 