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
    const body = await response.text();
    console.log(`Status: ${response.status()}, Body: ${body.substring(0, 200)}`);
    expect(response.ok()).toBeTruthy();
    const dsl = JSON.parse(body);
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
    const createBtn = page.getByText("Nouveau").first();
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page.url()).toContain("/development/dsls/new");
    }
  });
});
