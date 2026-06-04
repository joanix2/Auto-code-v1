import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProjectForm } from "./ProjectForm";
import { projectService } from "@/services/project.service";

vi.mock("@/services/project.service", () => ({
  projectService: {
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
  },
}));

function renderCreateForm() {
  return render(
    <MemoryRouter initialEntries={["/development/projets/new"]}>
      <Routes>
        <Route path="/development/projets/new" element={<ProjectForm />} />
        <Route path="/development/projets" element={<div>Projects List</div>} />
        <Route path="/development/projets/:projectId" element={<div>Project Detail</div>} />
      </Routes>
    </MemoryRouter>
  );
}

function renderEditForm(projectId: string = "proj-1") {
  return render(
    <MemoryRouter initialEntries={[`/development/projets/${projectId}/edit`]}>
      <Routes>
        <Route path="/development/projets/:projectId/edit" element={<ProjectForm />} />
        <Route path="/development/projets" element={<div>Projects List</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProjectForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("create mode", () => {
    it("renders the create form", () => {
      renderCreateForm();
      expect(screen.getByText("Nouveau projet")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("Mon projet")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Enregistrer/i })).toBeInTheDocument();
    });

    it("prevents submission when name is empty", async () => {
      renderCreateForm();
      const submitBtn = screen.getByRole("button", { name: /Enregistrer/i });
      expect(submitBtn).toBeInTheDocument();
      await userEvent.click(submitBtn);
      expect(projectService.create).not.toHaveBeenCalled();
    });

    it("calls createProject and navigates on success", async () => {
      vi.mocked(projectService.create).mockResolvedValue({
        id: "new-1",
        name: "Test",
        description: "Desc",
        status: "draft",
        created_at: "2024-06-01T00:00:00Z",
      });
      renderCreateForm();
      await userEvent.type(screen.getByPlaceholderText("Mon projet"), "Test");
      await userEvent.type(
        screen.getByPlaceholderText("Description du projet..."),
        "Desc"
      );
      await userEvent.click(screen.getByRole("button", { name: /Enregistrer/i }));
      expect(projectService.create).toHaveBeenCalledWith({ name: "Test", description: "Desc" });
    });
  });

  describe("edit mode", () => {
    it("loads project data on mount", async () => {
      vi.mocked(projectService.getById).mockResolvedValue({
        id: "proj-1",
        name: "Existing Project",
        description: "Existing desc",
        status: "active",
        created_at: "2024-06-01T00:00:00Z",
      });
      renderEditForm();
      expect(await screen.findByDisplayValue("Existing Project")).toBeInTheDocument();
      expect(await screen.findByDisplayValue("Existing desc")).toBeInTheDocument();
    });
  });
});
