import { test, expect } from "@playwright/test";
import { createProject, cleanupProjects } from "./helpers/api";
import { loginAsTestUser } from "./helpers/auth";

test.describe("Projects UI (e2e)", () => {
  let projectId: string;

  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
    await cleanupProjects();
  });

  test.afterEach(async () => {
    await cleanupProjects();
  });

  test("projects page loads and shows title", async ({ page }) => {
    await page.goto("/development/projets");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("Projets").first()).toBeVisible();
  });

  test("can see a created project in the list", async ({ page }) => {
    const project = await createProject(`UI Test ${Date.now()}`);
    projectId = project.id;

    await page.goto("/development/projets");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(project.name).first()).toBeVisible();
  });

  test("project detail page shows tab buttons in header", async ({ page }) => {
    const project = await createProject(`Tab Test ${Date.now()}`);
    projectId = project.id;

    await page.goto(`/development/projets/${project.id}`);
    await page.waitForLoadState("networkidle");

    expect(page.url()).toContain(`/development/projets/${project.id}`);

    await expect(page.getByText("Tickets").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Ontologie").first()).toBeVisible();
    await expect(page.getByText("Architecture").first()).toBeVisible();
    await expect(page.getByText("Déploiement").first()).toBeVisible();
    await expect(page.getByText("Monitoring").first()).toBeVisible();
  });

  test("can switch between tabs to see different content", async ({ page }) => {
    const project = await createProject(`Switch Test ${Date.now()}`);
    projectId = project.id;

    await page.goto(`/development/projets/${project.id}`);
    await page.waitForLoadState("networkidle");

    expect(page.url()).toContain(`/development/projets/${project.id}`);

    const tabs = [
      { name: "Tickets", expected: "Tous" },
      { name: "Ontologie", expected: "Graphe d'ontologie" },
      { name: "Architecture", expected: "Modèles d'architecture" },
      { name: "Déploiement", expected: "Déploiement continu" },
      { name: "Monitoring", expected: "Monitoring" },
    ];

    for (const tab of tabs) {
      const tabButton = page.getByText(tab.name).first();
      await expect(tabButton).toBeVisible({ timeout: 3000 });
      await tabButton.click();
      await page.waitForTimeout(500);
      await expect(page.getByText(tab.expected).first()).toBeVisible({ timeout: 3000 });
    }
  });
});
