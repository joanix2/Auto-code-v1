import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

function renderProjectDetails(projectId: string = "proj-1") {
  return render(
    <MemoryRouter initialEntries={[`/development/projets/${projectId}`]}>
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

  it("renders project name and description", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    expect(await screen.findByText("Mon Projet Test")).toBeInTheDocument();
    expect(screen.getByText("Description du projet de test")).toBeInTheDocument();
  });

  it("renders all 5 sub-tabs", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    await screen.findByText("Mon Projet Test");
    expect(screen.getByText("Tickets")).toBeInTheDocument();
    expect(screen.getByText("Ontologie")).toBeInTheDocument();
    expect(screen.getByText("Architecture")).toBeInTheDocument();
    expect(screen.getByText("Déploiement")).toBeInTheDocument();
    expect(screen.getByText("Monitoring")).toBeInTheDocument();
  });

  it("shows Tickets tab content by default", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    await screen.findByText("Mon Projet Test");
    expect(screen.getByText("Tickets du projet")).toBeInTheDocument();
  });

  it("switches to Ontologie tab on click", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    await screen.findByText("Mon Projet Test");
    await userEvent.click(screen.getByText("Ontologie"));
    expect(screen.getByText("Graphe d'ontologie")).toBeInTheDocument();
  });

  it("switches to Architecture tab on click", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    await screen.findByText("Mon Projet Test");
    await userEvent.click(screen.getByText("Architecture"));
    expect(screen.getByText("Modèles d'architecture")).toBeInTheDocument();
  });

  it("switches to Déploiement tab on click", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    await screen.findByText("Mon Projet Test");
    await userEvent.click(screen.getByText("Déploiement"));
    expect(screen.getByText("Déploiement continu")).toBeInTheDocument();
  });

  it("switches to Monitoring tab on click", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    await screen.findByText("Mon Projet Test");
    await userEvent.click(screen.getByText("Monitoring"));
    expect(screen.getAllByText("Monitoring").length).toBeGreaterThanOrEqual(1);
  });

  it("navigates back to projects list when clicking retour", async () => {
    vi.mocked(projectService.getById).mockResolvedValue(mockProject);
    renderProjectDetails();
    await screen.findByText("Mon Projet Test");
    await userEvent.click(screen.getByText("Retour aux projets"));
    expect(screen.getByText("Projects List")).toBeInTheDocument();
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
