/**
 * useIssues Hook - Manage issues state and actions
 */
import { useState, useEffect, useCallback } from 'react';
import { Issue } from '../types';
import { issueService } from '../services/issue.service';

export function useIssues(repositoryId?: string) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (repositoryId) {
      loadIssues();
    }
  }, [repositoryId]);

  const loadIssues = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await issueService.getAll(repositoryId);
      setIssues(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [repositoryId]);

  const assignToCopilot = useCallback(async (issueId: string, options?: { base_branch?: string; custom_instructions?: string }) => {
    setLoading(true);
    setError(null);
    try {
      await issueService.assignToCopilot(issueId, options);
      await loadIssues();
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadIssues]);

  const deleteIssue = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await issueService.delete(id);
      setIssues((prev) => prev.filter((issue) => issue.id !== id));
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    issues,
    loading,
    error,
    loadIssues,
    assignToCopilot,
    deleteIssue,
  };
}
