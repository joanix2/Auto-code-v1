/**
 * useMessages Hook - Manage messages state and actions
 */
import { useState, useEffect, useCallback } from 'react';
import { Message, MessageCreate } from '../types';
import { messageService } from '../services/message.service';

export function useMessages(issueId?: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (issueId) {
      loadMessages();
    }
  }, [issueId]);

  const loadMessages = useCallback(async () => {
    if (!issueId) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await messageService.getByIssue(issueId);
      setMessages(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [issueId]);

  const sendMessage = useCallback(async (content: string, author_username: string) => {
    if (!issueId) return;

    setLoading(true);
    setError(null);
    try {
      const newMessage = await messageService.create({
        issue_id: issueId,
        content,
        author_username,
        author_type: 'user',
      });
      setMessages((prev) => [...prev, newMessage]);
      return newMessage;
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [issueId]);

  const deleteMessage = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await messageService.delete(id);
      setMessages((prev) => prev.filter((msg) => msg.id !== id));
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    messages,
    loading,
    error,
    loadMessages,
    sendMessage,
    deleteMessage,
  };
}
