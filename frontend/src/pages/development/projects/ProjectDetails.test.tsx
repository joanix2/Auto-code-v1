import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProjectDetails } from "./ProjectDetails";
import { projectService } from "@/services/project.service";

vi.mock("@/services/project.service", () => ({
  projectService: {
    getAll: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockProject = {
  id: "proj-1",
  name: "Mon Projet Test",
  description: "Description du projet de test",
  status: "active",
  created_at: "2024-06-01T00:00:00Z",
  updated_at: "2024-06-10T00:00:00Z",
};

function renderProjectDetails(projectId: string = "proj-1", tab: string = "tickets") {
  return render(
    <MemoryRouter initialEntries={[`/development/projets/${projectId}?tab=${tab}`]}>
      <Routes>
        <Route path="/development/projets/:projectId" element={<ProjectDetails />} />
        <Route path="/development/projets" element={<div>Projects List</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProjectDetails page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders tickets content by default", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    expect(await screen.findByText("Tous")).toBeInTheDocument();
  });

  it("shows ontologie content when tab=ontologie", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails("proj-1", "ontologie");
    expect(await screen.findByText(/créer un nœud/)).toBeInTheDocument();
  });

  it("shows architecture content when tab=architecture", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails("proj-1", "architecture");
    expect(await screen.findByText("Architecture")).toBeInTheDocument();
  });

  it("shows deploiement content when tab=deploiement", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails("proj-1", "deploiement");
    expect(await screen.findByText("Déploiement continu")).toBeInTheDocument();
  });

  it("shows monitoring content when tab=monitoring", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails("proj-1", "monitoring");
    const monitoring = await screen.findAllByText("Monitoring");
    expect(monitoring.length).toBeGreaterThanOrEqual(1);
  });

  it("shows loading state while fetching project", async () => {
    vi.mocked(projectService.getById).mockImplementation(() => new Promise(() => {}));
    renderProjectDetails();
    expect(screen.getByText("Chargement...")).toBeInTheDocument();
  });

  it("navigates to projects list when project fetch fails", async () => {
    vi.mocked(projectService.getById).mockRejectedValue(new Error("Not found"));
    renderProjectDetails();
    expect(await screen.findByText("Projects List")).toBeInTheDocument();
  });
});
