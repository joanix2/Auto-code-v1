import { describe, it, expect, vi, beforeEach } from "vitest";
import { projectService } from "./project.service";
import { apiService } from "./api.service";

vi.mock("./api.service", () => ({
  apiService: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
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

describe("ProjectService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getAll calls apiService.get with correct path", async () => {
    vi.mocked(apiService.get).mockResolvedValue([mockProject]);
    const result = await projectService.getAll();
    expect(apiService.get).toHaveBeenCalledWith("/api/projects", { params: undefined });
    expect(result).toEqual([mockProject]);
  });

  it("getById calls apiService.get with id", async () => {
    vi.mocked(apiService.get).mockResolvedValue(mockProject);
    const result = await projectService.getById("1");
    expect(apiService.get).toHaveBeenCalledWith("/api/projects/1");
    expect(result).toEqual(mockProject);
  });

  it("create sends POST with data", async () => {
    const createData = { name: "New Project", description: "Desc" };
    vi.mocked(apiService.post).mockResolvedValue({ id: "2", ...createData, status: "draft", created_at: "2024-06-01T00:00:00Z" });
    const result = await projectService.create(createData);
    expect(apiService.post).toHaveBeenCalledWith("/api/projects", createData);
    expect(result.name).toBe("New Project");
  });

  it("update sends PUT with id and data", async () => {
    const updateData = { name: "Updated" };
    vi.mocked(apiService.put).mockResolvedValue({ ...mockProject, ...updateData });
    const result = await projectService.update("1", updateData);
    expect(apiService.put).toHaveBeenCalledWith("/api/projects/1", updateData);
    expect(result.name).toBe("Updated");
  });

  it("delete sends DELETE with id", async () => {
    vi.mocked(apiService.delete).mockResolvedValue(undefined);
    await projectService.delete("1");
    expect(apiService.delete).toHaveBeenCalledWith("/api/projects/1");
  });
});
