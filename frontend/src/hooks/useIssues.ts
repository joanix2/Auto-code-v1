/**
 * useIssues Hook - Manage issues state and actions
 */
import { useState, useEffect, useCallback } from "react";
import { Issue, IssueCreate, IssueUpdate } from "../types";
import { issueService } from "../services/issue.service";

export function useIssues(repositoryId?: string) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadIssues = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await issueService.getAllIssues(repositoryId);
      setIssues(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [repositoryId]);

  useEffect(() => {
    loadIssues();
  }, [loadIssues]);

  const getIssue = useCallback(async (issueId: string): Promise<Issue> => {
    setLoading(true);
    setError(null);
    try {
      const issue = await issueService.getById(issueId);
      return issue;
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createIssue = useCallback(async (data: IssueCreate): Promise<Issue> => {
    setLoading(true);
    setError(null);
    try {
      const newIssue = await issueService.create(data);
      setIssues((prev) => [newIssue, ...prev]);
      return newIssue;
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateIssue = useCallback(async (issueId: string, data: IssueUpdate): Promise<Issue> => {
    setLoading(true);
    setError(null);
    try {
      const updatedIssue = await issueService.update(issueId, data);
      setIssues((prev) => prev.map((issue) => (issue.id === issueId ? updatedIssue : issue)));
      return updatedIssue;
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const assignToCopilot = useCallback(
    async (issueId: string, options?: { base_branch?: string; custom_instructions?: string }) => {
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
    },
    [loadIssues]
  );

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

  const syncIssues = useCallback(async () => {
    if (!repositoryId) {
      setError("Cannot sync issues without a repository ID");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Use IssueService.sync() instead of RepositoryService
      await issueService.sync({ repositoryId });
      // Reload issues after sync
      await loadIssues();
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [repositoryId, loadIssues]);

  return {
    issues,
    loading,
    error,
    loadIssues,
    getIssue,
    createIssue,
    updateIssue,
    assignToCopilot,
    deleteIssue,
    syncIssues,
  };
}
