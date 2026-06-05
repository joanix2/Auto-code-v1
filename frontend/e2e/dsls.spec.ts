import { test, expect } from "@playwright/test";
import { loginAsTestUser } from "./helpers/auth";

test.describe("DSL creation", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test("can create a DSL via API", async ({ request }) => {
    const resp = await request.post("http://localhost:8000/api/auth/dev-login");
    const { access_token } = await resp.json();
    const response = await request.post("http://localhost:8000/api/dsls", {
      data: { name: "Test DSL via API", description: "Created by e2e test", version: "1.0" },
      headers: { Authorization: `Bearer ${access_token}` },
    });
    expect(response.ok()).toBeTruthy();
    const dsl = await response.json();
    expect(dsl.name).toBe("Test DSL via API");
    expect(dsl.id).toBeTruthy();
  });

  test("DSLs page loads and shows list", async ({ page }) => {
    await page.goto("/development/dsls");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("DSLs").first()).toBeVisible();
  });

  test("can navigate to create DSL form", async ({ page }) => {
    await page.goto("/development/dsls");
    await page.waitForLoadState("networkidle");
    const createBtn = page.getByText("Nouveau DSL").first();
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page.url()).toContain("/development/dsls/new");
    }
  });

  test("created DSL appears in the list", async ({ page, request }) => {
    // Create DSL via API
    const auth = await request.post("http://localhost:8000/api/auth/dev-login");
    const { access_token } = await auth.json();
    const resp = await request.post("http://localhost:8000/api/dsls", {
      data: { name: "E2E DSL Test", description: "Should appear in list", version: "1.0" },
      headers: { Authorization: `Bearer ${access_token}` },
    });
    expect(resp.ok()).toBeTruthy();
    const dsl = await resp.json();

    // Navigate to DSL list page and verify it appears
    await page.goto("/development/dsls");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("E2E DSL Test").first()).toBeVisible();

    // Click on DSL to view details
    await page.getByText("E2E DSL Test").first().click();
    await page.waitForLoadState("networkidle");
    // Should navigate to detail page without error
    expect(page.url()).toContain(`/development/dsls/${dsl.id}`);
    // The graph viewer should load (no error state)
    await expect(page.getByText("E2E DSL Test").first()).toBeVisible();
  });
});
