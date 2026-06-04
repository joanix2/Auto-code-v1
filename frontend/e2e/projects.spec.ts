import { test, expect } from "@playwright/test";
import { createProject, deleteProject, getProjects, cleanupProjects } from "./helpers/api";

test.describe("Projects (e2e)", () => {
  let createdProjectId: string | null = null;
  let projectName: string;

  test.beforeEach(() => {
    projectName = `E2E Test ${Date.now()}`;
  });

  test.afterEach(async () => {
    // Cleanup: delete all test projects created during this run
    await cleanupProjects();
  });

  test("can list projects from the API", async () => {
    const projects = await getProjects();
    expect(Array.isArray(projects)).toBeTruthy();
  });

  test("can create a project via API", async () => {
    const project = await createProject(projectName, "Created by e2e test");
    createdProjectId = project.id;
    expect(project.name).toBe(projectName);
    expect(project.id).toBeTruthy();
    expect(project.status).toBeDefined();
  });

  test("can delete a project via API", async () => {
    const project = await createProject(projectName, "To be deleted");
    await deleteProject(project.id);
    const projects = await getProjects();
    expect(projects.find((p: any) => p.id === project.id)).toBeUndefined();
  });
});
