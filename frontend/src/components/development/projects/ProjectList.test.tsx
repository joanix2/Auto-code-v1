import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProjectList } from "./ProjectList";
import { Project } from "@/types/project";

const mockProjects: Project[] = [
  { id: "1", name: "Projet A", status: "active", created_at: "2024-06-01T00:00:00Z" },
  { id: "2", name: "Projet B", description: "Second project", status: "draft", created_at: "2024-06-02T00:00:00Z" },
];

describe("ProjectList", () => {
  it("renders all projects", () => {
    render(<ProjectList items={mockProjects} />);
    expect(screen.getByText("Projet A")).toBeInTheDocument();
    expect(screen.getByText("Projet B")).toBeInTheDocument();
  });

  it("renders empty message when no projects", () => {
    render(<ProjectList items={[]} />);
    expect(screen.getByText("Aucun projet. Créez votre premier projet pour commencer.")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    render(<ProjectList items={[]} loading={true} />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders create button when createUrl provided", () => {
    render(<ProjectList items={mockProjects} createUrl="/development/projets/new" />);
    expect(screen.getByText("Nouveau projet")).toBeInTheDocument();
  });

  it("filters projects by search query", async () => {
    render(<ProjectList items={mockProjects} />);
    const searchInput = screen.getByPlaceholderText("Search...");
    // Type in search
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
    nativeInputValueSetter?.call(searchInput, "Projet A");
    searchInput.dispatchEvent(new Event("input", { bubbles: true }));
    expect(screen.getByText("Projet A")).toBeInTheDocument();
    expect(screen.queryByText("Projet B")).not.toBeInTheDocument();
  });
});
