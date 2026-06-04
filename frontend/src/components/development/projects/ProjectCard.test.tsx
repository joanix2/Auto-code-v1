import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProjectCard } from "./ProjectCard";
import { Project } from "@/types/project";

const mockProject: Project = {
  id: "1",
  name: "Mon Projet",
  description: "Description du projet",
  status: "active",
  created_at: "2024-06-01T00:00:00Z",
  updated_at: "2024-06-10T00:00:00Z",
};

const mockProjectDraft: Project = {
  id: "2",
  name: "Brouillon",
  status: "draft",
  created_at: "2024-06-01T00:00:00Z",
};

describe("ProjectCard", () => {
  it("renders project name and description", () => {
    render(<ProjectCard data={mockProject} />);
    expect(screen.getByText("Mon Projet")).toBeInTheDocument();
    expect(screen.getByText("Description du projet")).toBeInTheDocument();
  });

  it("renders status badge for active project", () => {
    render(<ProjectCard data={mockProject} />);
    expect(screen.getByText("Actif")).toBeInTheDocument();
  });

  it("renders status badge for draft project", () => {
    render(<ProjectCard data={mockProjectDraft} />);
    const badges = screen.getAllByText("Brouillon");
    expect(badges.length).toBe(2);
  });

  it("renders created date", () => {
    render(<ProjectCard data={mockProject} />);
    expect(screen.getByText((content) => content.includes("Jun 1, 2024"))).toBeInTheDocument();
  });

  it("calls onClick when card is clicked", () => {
    const onClick = vi.fn();
    const { container } = render(<ProjectCard data={mockProject} onClick={onClick} />);
    const card = container.querySelector("[data-slot='card']") || container.querySelector("div");
    card?.click();
    // BaseCard wraps in a clickable div
    expect(onClick).toHaveBeenCalledWith("1");
  });

  it("renders description fallback when not provided", () => {
    render(<ProjectCard data={mockProjectDraft} />);
    expect(screen.getByText("Aucune description")).toBeInTheDocument();
  });
});
