import { useState, useEffect, useCallback } from "react";
import { Project, ProjectCreate, ProjectUpdate } from "../types/project";
import { projectService } from "../services/project.service";

interface ApiError {
  detail?: string;
  message?: string;
}

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await projectService.getAll();
      setProjects(data);
    } catch (err) {
      setError((err as ApiError)?.detail || (err as Error)?.message || "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const createProject = useCallback(async (data: ProjectCreate): Promise<Project> => {
    setLoading(true);
    setError(null);
    try {
      const project = await projectService.create(data);
      setProjects((prev) => [project, ...prev]);
      return project;
    } catch (err) {
      setError((err as ApiError)?.detail || (err as Error)?.message || "Failed to create project");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProject = useCallback(async (id: string, data: ProjectUpdate): Promise<Project> => {
    setLoading(true);
    setError(null);
    try {
      const project = await projectService.update(id, data);
      setProjects((prev) => prev.map((p) => (p.id === id ? project : p)));
      return project;
    } catch (err) {
      setError((err as ApiError)?.detail || (err as Error)?.message || "Failed to update project");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteProject = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await projectService.delete(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      setError((err as ApiError)?.detail || (err as Error)?.message || "Failed to delete project");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getProject = useCallback(async (id: string): Promise<Project> => {
    setLoading(true);
    setError(null);
    try {
      const project = await projectService.getById(id);
      return project;
    } catch (err) {
      setError((err as ApiError)?.detail || (err as Error)?.message || "Failed to load project");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    projects,
    loading,
    error,
    loadProjects,
    createProject,
    updateProject,
    deleteProject,
    getProject,
  };
}
