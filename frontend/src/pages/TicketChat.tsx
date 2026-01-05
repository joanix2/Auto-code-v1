import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { AppBar } from "@/components/AppBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowLeft, Send, Loader2 } from "lucide-react";
import type { Ticket, Message } from "@/types";
import { TicketStatus } from "@/types";

export function TicketChat() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch ticket details
  useEffect(() => {
    const fetchTicket = async () => {
      if (!ticketId) return;

      try {
        const data = await apiClient.getTicket(ticketId);
        setTicket(data);
      } catch (err) {
        console.error("Error fetching ticket:", err);
        setError((err as Error).message || "Failed to load ticket");
      }
    };

    fetchTicket();
  }, [ticketId]);

  // Fetch messages
  useEffect(() => {
    const fetchMessages = async () => {
      if (!ticketId) return;

      try {
        setLoading(true);
        const data = await apiClient.getTicketMessages(ticketId);
        setMessages(data);
      } catch (err) {
        console.error("Error fetching messages:", err);
        setError((err as Error).message || "Failed to load messages");
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
  }, [ticketId]);

  // Send message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newMessage.trim() || !ticketId) return;

    try {
      setSending(true);
      setError("");

      const messageData = {
        ticket_id: ticketId,
        role: "user" as const,
        content: newMessage.trim(),
        metadata: {
          sender: user?.username,
        },
      };

      const createdMessage = await apiClient.createMessage(messageData);

      // Add the new message to the list
      setMessages((prev) => [...prev, createdMessage]);
      setNewMessage("");

      // TODO: Trigger AI response here if needed
      // This could call the ticket processing endpoint to get an AI response
    } catch (err) {
      console.error("Error sending message:", err);
      setError((err as Error).message || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  // Get role display info
  const getRoleInfo = (role: string) => {
    switch (role) {
      case "user":
        return {
          icon: "👤",
          color: "bg-blue-500",
          textColor: "text-blue-700",
          bgColor: "bg-blue-50",
        };
      case "assistant":
        return {
          icon: "🤖",
          color: "bg-purple-500",
          textColor: "text-purple-700",
          bgColor: "bg-purple-50",
        };
      case "system":
        return {
          icon: "⚙️",
          color: "bg-gray-500",
          textColor: "text-gray-700",
          bgColor: "bg-gray-50",
        };
      default:
        return {
          icon: "💬",
          color: "bg-gray-500",
          textColor: "text-gray-700",
          bgColor: "bg-gray-50",
        };
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AppBar />
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <AppBar />

      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Header */}
        <div className="mb-6">
          <Button variant="ghost" onClick={() => navigate(-1)} className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          {ticket && (
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-2xl mb-2">{ticket.title}</CardTitle>
                    {ticket.description && <p className="text-gray-600 text-sm">{ticket.description}</p>}
                  </div>
                  <div className="ml-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        ticket.status === TicketStatus.CLOSED
                          ? "bg-green-100 text-green-800"
                          : ticket.status === TicketStatus.IN_PROGRESS
                          ? "bg-blue-100 text-blue-800"
                          : ticket.status === TicketStatus.CANCELLED
                          ? "bg-red-100 text-red-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {ticket.status}
                    </span>
                  </div>
                </div>
              </CardHeader>
            </Card>
          )}
        </div>

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Chat Container */}
        <Card className="h-[calc(100vh-300px)] flex flex-col">
          <CardHeader className="border-b">
            <CardTitle className="text-lg">Conversation</CardTitle>
          </CardHeader>

          {/* Messages */}
          <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <p className="mb-2">No messages yet</p>
                  <p className="text-sm">Start the conversation by sending a message below</p>
                </div>
              ) : (
                messages.map((message) => {
                  const roleInfo = getRoleInfo(message.role);
                  const isUser = message.role === "user";

                  return (
                    <div key={message.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[70%] ${isUser ? "order-2" : "order-1"}`}>
                        <div className={`rounded-lg p-4 ${isUser ? "bg-blue-500 text-white" : roleInfo.bgColor}`}>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-lg">{roleInfo.icon}</span>
                            <span className={`text-xs font-medium ${isUser ? "text-blue-100" : roleInfo.textColor}`}>{message.role.charAt(0).toUpperCase() + message.role.slice(1)}</span>
                            {message.step && <span className={`text-xs px-2 py-0.5 rounded ${isUser ? "bg-blue-600 text-blue-100" : "bg-gray-200 text-gray-700"}`}>{message.step}</span>}
                          </div>

                          <p className={`text-sm whitespace-pre-wrap ${isUser ? "text-white" : "text-gray-800"}`}>{message.content}</p>

                          <div className={`mt-2 text-xs ${isUser ? "text-blue-100" : "text-gray-500"}`}>
                            {formatTimestamp(message.timestamp)}
                            {message.model && <span className="ml-2">• {message.model}</span>}
                            {message.tokens_used && <span className="ml-2">• {message.tokens_used} tokens</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input */}
          <CardContent className="border-t p-4">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <Input value={newMessage} onChange={(e) => setNewMessage(e.target.value)} placeholder="Type your message..." disabled={sending} className="flex-1" autoFocus />
              <Button type="submit" disabled={sending || !newMessage.trim()}>
                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
