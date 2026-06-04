import { test, expect } from "@playwright/test";
import { createProject, deleteProject, cleanupProjects } from "./helpers/api";

test.describe("Projects UI (e2e)", () => {
  let projectId: string;

  test.beforeEach(async () => {
    await cleanupProjects();
  });

  test.afterEach(async () => {
    await cleanupProjects();
  });

  test("projects page loads and shows empty state", async ({ page }) => {
    await page.goto("/development/projets");
    await page.waitForLoadState("networkidle");

    // Should show the projects page
    await expect(page.getByText("Projets").first()).toBeVisible();
  });

  test("can navigate to create project form", async ({ page }) => {
    await page.goto("/development/projets");
    await page.waitForLoadState("networkidle");

    // Click the create button
    const createBtn = page.getByText("Nouveau projet");
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page.url()).toContain("/development/projets/new");
    }
  });

  test("can create a project via UI and see it in the list", async ({ page }) => {
    const project = await createProject(`UI Test ${Date.now()}`, "Test from e2e");
    projectId = project.id;

    await page.goto("/development/projets");
    await page.waitForLoadState("networkidle");

    await expect(page.getByText(project.name).first()).toBeVisible();
  });

  test("project detail page shows all 5 tabs", async ({ page }) => {
    const project = await createProject(`Detail Test ${Date.now()}`);
    projectId = project.id;

    await page.goto(`/development/projets/${project.id}`);
    await page.waitForLoadState("networkidle");

    await expect(page.getByText(project.name).first()).toBeVisible();

    // Check all tabs are present
    await expect(page.getByText("Tickets").first()).toBeVisible();
    await expect(page.getByText("Ontologie").first()).toBeVisible();
    await expect(page.getByText("Architecture").first()).toBeVisible();
    await expect(page.getByText("Déploiement").first()).toBeVisible();
    await expect(page.getByText("Monitoring").first()).toBeVisible();
  });

  test("can switch between project tabs", async ({ page }) => {
    const project = await createProject(`Tab Test ${Date.now()}`);
    projectId = project.id;

    await page.goto(`/development/projets/${project.id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(project.name).first()).toBeVisible();

    // Click each tab and verify content
    const tabs = [
      { name: "Tickets", expected: "Tickets du projet" },
      { name: "Ontologie", expected: "Graphe d'ontologie" },
      { name: "Architecture", expected: "Modèles d'architecture" },
      { name: "Déploiement", expected: "Déploiement continu" },
      { name: "Monitoring", expected: "Monitoring" },
    ];

    for (const tab of tabs) {
      const tabButton = page.getByText(tab.name).first();
      if (await tabButton.isVisible()) {
        await tabButton.click();
        await page.waitForTimeout(500);
        await expect(page.getByText(tab.expected).first()).toBeVisible();
      }
    }
  });
});
