/**
 * useRepositories Hook - Manage repositories state and actions
 */
import { useState, useEffect, useCallback } from "react";
import { Repository } from "../types";
import { repositoryService } from "../services/repository.service";

interface ApiError {
  detail?: string;
  message?: string;
}

export function useRepositories() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRepositories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await repositoryService.getAll();
      setRepositories(data);
    } catch (err) {
      const errorMessage = (err as ApiError)?.detail || (err as Error)?.message || "Failed to load repositories";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load repositories on mount
  useEffect(() => {
    loadRepositories();
  }, [loadRepositories]);

  const syncRepositories = useCallback(async (username?: string) => {
    setLoading(true);
    setError(null);
    try {
      // Use the new sync() method from SyncableService
      const response = await repositoryService.sync({ username });
      const data = response.data || [];
      setRepositories(data);
      return data;
    } catch (err) {
      const errorMessage = (err as ApiError)?.detail || (err as Error)?.message || "Failed to sync repositories";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * @deprecated Use IssueService.sync() through useIssues hook instead
   */
  const syncIssues = useCallback(async (repositoryId: string) => {
    setLoading(true);
    setError(null);
    try {
      await repositoryService.syncIssues(repositoryId);
    } catch (err) {
      const errorMessage = (err as ApiError)?.detail || (err as Error)?.message || "Failed to sync issues";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteRepository = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await repositoryService.delete(id);
      setRepositories((prev) => prev.filter((repo) => repo.id !== id));
    } catch (err) {
      const errorMessage = (err as ApiError)?.detail || (err as Error)?.message || "Failed to delete repository";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    repositories,
    loading,
    error,
    loadRepositories,
    syncRepositories,
    syncIssues,
    deleteRepository,
  };
}
