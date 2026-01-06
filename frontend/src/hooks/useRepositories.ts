/**
 * useRepositories Hook - Manage repositories state and actions
 */
import { useState, useEffect, useCallback } from 'react';
import { Repository } from '../types';
import { repositoryService } from '../services/repository.service';

export function useRepositories() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load repositories on mount
  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await repositoryService.getAll();
      setRepositories(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const syncRepositories = useCallback(async (username?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await repositoryService.syncRepositories(username);
      setRepositories(data);
      return data;
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const syncIssues = useCallback(async (repositoryId: string) => {
    setLoading(true);
    setError(null);
    try {
      await repositoryService.syncIssues(repositoryId);
    } catch (err) {
      setError((err as Error).message);
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
      setError((err as Error).message);
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
