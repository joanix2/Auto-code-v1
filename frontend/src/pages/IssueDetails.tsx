import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMessages } from "@/hooks/useMessages";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Send, User, Bot } from "lucide-react";

export function IssueDetails() {
  const { issueId } = useParams<{ issueId: string }>();
  const navigate = useNavigate();
  const { messages, loading, sendMessage, deleteMessage } = useMessages(issueId || "");
  const [newMessage, setNewMessage] = React.useState("");
  const [sending, setSending] = React.useState(false);

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !issueId) return;

    setSending(true);
    try {
      // TODO: Get actual username from auth context
      await sendMessage(newMessage, "current-user");
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

  const getAuthorIcon = (authorType: string) => {
    switch (authorType) {
      case "copilot":
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
        return <Badge className="bg-purple-100 text-purple-800">Copilot</Badge>;
      case "user":
        return <Badge className="bg-blue-100 text-blue-800">User</Badge>;
      default:
        return <Badge variant="outline">System</Badge>;
    }
  };

  return (
    <div className="container mx-auto max-w-4xl">
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h1 className="text-3xl font-bold text-gray-900">Issue Conversation</h1>
        <p className="mt-2 text-sm text-gray-600">Chat with Copilot about this issue</p>
      </div>

      <div className="space-y-4">
        {/* Messages List */}
        <div className="space-y-3">
          {loading && messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">Loading messages...</div>
          ) : messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No messages yet. Start the conversation!</div>
          ) : (
            messages.map((message) => (
              <Card key={message.id} className="relative">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getAuthorIcon(message.author_type)}
                      <CardTitle className="text-base">{message.author_username || "System"}</CardTitle>
                      {getAuthorBadge(message.author_type)}
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => handleDeleteMessage(message.id)} className="text-red-600 hover:text-red-700">
                      Delete
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{message.content}</p>
                  <p className="mt-2 text-xs text-gray-500">{new Date(message.created_at).toLocaleString()}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Message Input */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <Textarea placeholder="Type your message here..." value={newMessage} onChange={(e) => setNewMessage(e.target.value)} rows={4} disabled={sending} />
              <div className="flex justify-end">
                <Button onClick={handleSendMessage} disabled={!newMessage.trim() || sending}>
                  <Send className="h-4 w-4 mr-2" />
                  {sending ? "Sending..." : "Send Message"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
