import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useMessages } from "@/hooks/useMessages";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Send, User, Bot, AlertCircle } from "lucide-react";

export function Messages() {
  const { issueId } = useParams<{ issueId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { messages, loading, error, sendMessage, deleteMessage } = useMessages(issueId || "");
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!newMessage.trim() || !issueId) return;

    setSending(true);
    try {
      // Automatically prepend @copilote to the message if not already present
      const messageToSend = newMessage.trim().startsWith('@copilote') 
        ? newMessage 
        : `@copilote ${newMessage}`;
      
      await sendMessage(messageToSend, user?.username || "anonymous");
      setNewMessage("");
    } finally {
      setSending(false);
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    if (confirm("Are you sure you want to delete this message?")) {
      await deleteMessage(messageId);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getAuthorIcon = (authorType: string) => {
    switch (authorType) {
      case "copilot":
      case "assistant":
        return <Bot className="h-5 w-5 text-purple-600" />;
      case "user":
        return <User className="h-5 w-5 text-blue-600" />;
      default:
        return <User className="h-5 w-5 text-gray-600" />;
    }
  };

  const getAuthorBadge = (authorType: string) => {
    switch (authorType) {
      case "copilot":
      case "assistant":
        return <Badge className="bg-purple-100 text-purple-800">Copilot</Badge>;
      case "user":
        return <Badge className="bg-blue-100 text-blue-800">User</Badge>;
      case "system":
        return <Badge variant="outline">System</Badge>;
      default:
        return <Badge variant="outline">{authorType}</Badge>;
    }
  };

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

  return (
    <div className="container mx-auto max-w-4xl px-3 sm:px-4 py-4 sm:py-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-3 sm:mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Issues
        </Button>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Issue Conversation</h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">Chat with Copilot about this issue</p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Messages Container */}
      <div className="space-y-3 sm:space-y-4">
        {/* Messages List */}
        <div className="space-y-3 max-h-[calc(100vh-400px)] overflow-y-auto pr-2">
          {loading && messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">Loading messages...</div>
          ) : messages.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-500 font-medium">No messages yet</p>
                  <p className="text-sm text-gray-400 mt-2">Start the conversation by sending a message below!</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {messages.map((message) => {
                const isUser = message.author_type === "user";

                return (
                  <div key={message.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                    <Card className={`max-w-[80%] ${isUser ? "bg-blue-50 border-blue-200" : "bg-white"}`}>
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between gap-4">
                          <div className="flex items-center gap-2 flex-1">
                            {getAuthorIcon(message.author_type)}
                            <CardTitle className="text-sm font-medium">{message.author_username || "System"}</CardTitle>
                            {getAuthorBadge(message.author_type)}
                          </div>
                          {isUser && (
                            <Button variant="ghost" size="sm" onClick={() => handleDeleteMessage(message.id)} className="text-red-600 hover:text-red-700 h-8 px-2">
                              Delete
                            </Button>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{message.content}</p>
                        <div className="flex items-center gap-2 mt-3 text-xs text-gray-500">
                          <span>{formatTimestamp(message.created_at)}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Message Input */}
        <Card className="sticky bottom-0 shadow-lg">
          <CardContent className="pt-6">
            <form onSubmit={handleSendMessage} className="space-y-3">
              <Textarea
                placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                rows={4}
                disabled={sending}
                className="resize-none"
              />
              <div className="flex justify-between items-center">
                <p className="text-xs text-gray-500">{newMessage.length > 0 && `${newMessage.length} characters`}</p>
                <Button type="submit" onClick={handleSendMessage} disabled={!newMessage.trim() || sending}>
                  <Send className="h-4 w-4 mr-2" />
                  {sending ? "Sending..." : "Send Message"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
