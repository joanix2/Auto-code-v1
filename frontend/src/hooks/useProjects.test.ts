import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useProjects } from "./useProjects";
import { projectService } from "../services/project.service";

vi.mock("../services/project.service", () => ({
  projectService: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockProject = {
  id: "1",
  name: "Test Project",
  description: "A test project",
  status: "draft",
  created_at: "2024-06-01T00:00:00Z",
};

describe("useProjects", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches projects on mount", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue([mockProject]);
    const { result } = renderHook(() => useProjects());
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.projects).toEqual([mockProject]);
    expect(result.current.error).toBeNull();
  });

  it("handles fetch error", async () => {
    vi.mocked(projectService.getAll).mockRejectedValue(new Error("Network error"));
    const { result } = renderHook(() => useProjects());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.projects).toEqual([]);
    expect(result.current.error).toBe("Network error");
  });

  it("creates a project", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue([]);
    vi.mocked(projectService.create).mockResolvedValue(mockProject);
    const { result } = renderHook(() => useProjects());
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      const created = await result.current.createProject({ name: "Test Project" });
      expect(created).toEqual(mockProject);
    });
    expect(result.current.projects).toContainEqual(mockProject);
  });

  it("updates a project", async () => {
    const updated = { ...mockProject, name: "Updated" };
    vi.mocked(projectService.getAll).mockResolvedValue([mockProject]);
    vi.mocked(projectService.update).mockResolvedValue(updated);
    const { result } = renderHook(() => useProjects());
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      const res = await result.current.updateProject("1", { name: "Updated" });
      expect(res).toEqual(updated);
    });
    expect(result.current.projects[0].name).toBe("Updated");
  });

  it("deletes a project", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue([mockProject]);
    vi.mocked(projectService.delete).mockResolvedValue(undefined);
    const { result } = renderHook(() => useProjects());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.projects).toHaveLength(1);
    });
    await act(async () => {
      await result.current.deleteProject("1");
    });
    expect(result.current.projects).toHaveLength(0);
  });

  it("loadProjects reloads projects", async () => {
    vi.mocked(projectService.getAll).mockResolvedValueOnce([mockProject]);
    vi.mocked(projectService.getAll).mockResolvedValueOnce([]);
    const { result } = renderHook(() => useProjects());
    await waitFor(() => expect(result.current.projects).toHaveLength(1));
    await act(async () => {
      await result.current.loadProjects();
    });
    expect(result.current.projects).toHaveLength(0);
  });
});
