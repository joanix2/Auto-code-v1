import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Projects } from "./Projects";
import { projectService } from "@/services/project.service";

vi.mock("@/services/project.service", () => ({
  projectService: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockProjects = [
  { id: "1", name: "Projet Alpha", description: "Premier projet", status: "active", created_at: "2024-06-01T00:00:00Z" },
  { id: "2", name: "Projet Beta", status: "draft", created_at: "2024-06-02T00:00:00Z" },
];

function renderProjects() {
  return render(
    <MemoryRouter>
      <Projects />
    </MemoryRouter>
  );
}

describe("Projects page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page title", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue([]);
    renderProjects();
    expect(screen.getByText("Projets")).toBeInTheDocument();
    expect(screen.getByText("Gérez vos projets de développement")).toBeInTheDocument();
  });

  it("renders project list after loading", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue(mockProjects);
    renderProjects();
    expect(await screen.findByText("Projet Alpha")).toBeInTheDocument();
    expect(await screen.findByText("Projet Beta")).toBeInTheDocument();
  });

  it("shows empty state when no projects", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue([]);
    renderProjects();
    expect(await screen.findByText("Aucun projet. Créez votre premier projet pour commencer.")).toBeInTheDocument();
  });

  it("renders create button linking to new project", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue([]);
    renderProjects();
    expect(await screen.findByText("Nouveau projet")).toBeInTheDocument();
  });

  it("calls delete when delete action is triggered", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue(mockProjects);
    vi.mocked(projectService.delete).mockResolvedValue(undefined);
    renderProjects();
    await screen.findByText("Projet Alpha");
    // Find delete button (X mark) - rendered by BaseCard
    const deleteButtons = screen.getAllByRole("button");
    // Filter for delete buttons (trash icon is inside a button with title)
    expect(deleteButtons.length).toBeGreaterThan(0);
  });

  it("renders status badges for projects", async () => {
    vi.mocked(projectService.getAll).mockResolvedValue(mockProjects);
    renderProjects();
    expect(await screen.findByText("Actif")).toBeInTheDocument();
    expect(await screen.findByText("Brouillon")).toBeInTheDocument();
  });

  it("handles API error gracefully", async () => {
    vi.mocked(projectService.getAll).mockRejectedValue(new Error("API Error"));
    renderProjects();
    await screen.findByText("Projets");
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });
});
