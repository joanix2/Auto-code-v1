import { test, expect, request } from "@playwright/test";
import { loginAsTestUser } from "./helpers/auth";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";
const FRONTEND = process.env.FRONTEND_URL || "http://localhost:5173";

test.describe("Graph UI E2E", () => {
  let langId: string;

  test.beforeAll(async () => {
    // Creer un language avec des donnees via l'API
    const ctx = await request.newContext({ baseURL: BACKEND });
    const resp = await ctx.post("/api/languages", {
      data: { name: "e2e-ui-test", description: "UI test" },
    });
    const lang = await resp.json();
    langId = lang.id;

    // Ajouter des sorts
    for (const name of ["string", "int", "bool"]) {
      await ctx.post(`/api/languages/${langId}/sorts`, { data: { name } });
    }
    // Ajouter un op
    await ctx.post(`/api/languages/${langId}/ops`, {
      data: { name: "Ticket", result_sort: "string", params: ["string"] },
    });
  });

  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);

    // Intercept /api/auth/me pour eviter la verif Neo4j backend
    await page.route("**/api/auth/me", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: "e2e", username: "e2e", email: "e2e@test" }),
      });
    });
  });

  test("affiche le graphe avec les noeuds", async ({ page }) => {
    await page.goto(`/development/languages/${langId}`);
    await page.waitForLoadState("networkidle");

    // Le titre du language doit etre affiche
    await expect(page.getByText("e2e-ui-test").first()).toBeVisible({ timeout: 10000 });

    // Le conteneur du graphe contient le header avec les compteurs
    await expect(page.getByText(/nodes/).first()).toBeVisible();

    // Prendre une capture
    await page.screenshot({ path: "e2e/screenshots/graph-ui.png", fullPage: true });
  });

  test("les boutons de mode sont visibles", async ({ page }) => {
    await page.goto(`/development/languages/${langId}`);
    await page.waitForLoadState("networkidle");

    // Verifier que les 4 boutons de mode sont presents
    const toolbar = page.locator("div.absolute.top-2.right-2");
    await expect(toolbar).toBeVisible({ timeout: 5000 });

    // Boutons de mode
    await expect(page.getByTitle("Déplacer")).toBeVisible();
    await expect(page.getByTitle("Noeud")).toBeVisible();
    await expect(page.getByTitle("Arrête")).toBeVisible();
    await expect(page.getByTitle("Suppr.")).toBeVisible();

    // Boutons de zoom
    await expect(page.getByTitle("Zoom in")).toBeVisible();
    await expect(page.getByTitle("Zoom out")).toBeVisible();
  });

  test("le chat est visible en bas", async ({ page }) => {
    await page.goto(`/development/languages/${langId}`);
    await page.waitForLoadState("networkidle");

    const chatInput = page.getByPlaceholder("Demandez à l'IA de modifier le graphe...");
    await expect(chatInput).toBeVisible({ timeout: 5000 });
  });

  test("changer de mode met a jour l'UI", async ({ page }) => {
    await page.goto(`/development/languages/${langId}`);
    await page.waitForLoadState("networkidle");

    // Cliquer sur le bouton Noeud
    await page.getByTitle("Noeud").click();
    // Le mode node est actif (bouton sur fond accent)
    await expect(page.getByTitle("Noeud")).toHaveClass(/bg-accent/);

    // Cliquer sur Suppr.
    await page.getByTitle("Suppr.").click();
    await expect(page.getByTitle("Suppr.")).toHaveClass(/bg-accent/);

    // Revenir a Deplacer
    await page.getByTitle("Déplacer").click();
    await expect(page.getByTitle("Déplacer")).toHaveClass(/bg-accent/);
  });

  test.afterAll(async () => {
    // Nettoyer
    const ctx = await request.newContext({ baseURL: BACKEND });
    await ctx.delete(`/api/languages/${langId}`);
  });
});
