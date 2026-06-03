import { test, expect, Page } from "@playwright/test";

const API = "http://localhost:8000";

async function mockAuth(page: Page) {
  // Inject fake JWT
  await page.addInitScript(() => {
    localStorage.setItem("token", "e2e-test-token");
  });

  // Mock /api/auth/me to return a valid user
  await page.route(`${API}/api/auth/me`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "user-e2e",
        username: "testuser",
        email: "test@example.com",
        is_active: true,
        avatar_url: "",
      }),
    });
  });
}

test.describe("Metamodel E2E", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuth(page);
  });

  test("page des métamodèles se charge", async ({ page }) => {
    await page.goto("/metamodels");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();
  });

  test("créer un métamodèle via l'interface", async ({ page }) => {
    // Mock the metamodels list (empty)
    await page.route(`${API}/api/metamodels/`, async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
      } else if (route.request().method() === "POST") {
        const body = JSON.parse(route.request().postData() || "{}");
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: "mm-e2e-" + Date.now(),
            name: body.name,
            version: body.version || "1.0",
            description: body.description || "",
            status: "draft",
            owner_id: "testuser",
            created_at: new Date().toISOString(),
            allowed_node_types: [],
            allowed_edge_types: [],
          }),
        });
      }
    });

    await page.goto("/metamodels");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1500);

    // Try to click a create button (multiple possible labels)
    const createBtn = page.locator(
      'button:has-text("Créer"), button:has-text("Nouveau"), a:has-text("Créer"), [aria-label*="Créer"]'
    ).first();

    if (await createBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await createBtn.click();
      await page.waitForTimeout(500);
    }

    // Fill form fields
    const nameInput = page.locator('input[name="name"], input[id="name"], input[placeholder*="Nom"]').first();
    if (await nameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await nameInput.fill("Test-E2E-Playwright");
    }

    const versionInput = page.locator('input[name="version"], input[id="version"]').first();
    if (await versionInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await versionInput.fill("1.0");
    }

    // Submit
    const submitBtn = page.locator(
      'button[type="submit"], button:has-text("Créer"), button:has-text("Enregistrer"), button:has-text("Sauvegarder")'
    ).first();

    if (await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await Promise.all([
        page.waitForResponse((resp) => resp.url().includes("/api/metamodels/") && resp.status() === 201),
        submitBtn.click(),
      ]);
    }

    await page.waitForTimeout(1000);

    // Verify the new metamodel appears somewhere
    const created = page.locator("text=Test-E2E-Playwright");
    await expect(created.first()).toBeVisible({ timeout: 5000 });
  });
});
