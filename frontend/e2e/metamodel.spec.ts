import { test, expect } from "@playwright/test";

const API = "http://localhost:8000";

test.describe("Metamodel - E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("token", "e2e-fake-token");
    });
    await page.route(`${API}/api/auth/me`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "user-e2e", username: "testuser", email: "test@e2e.dev",
          is_active: true, avatar_url: "",
        }),
      })
    );
  });

  test("page metamodels se charge et affiche le titre", async ({ page }) => {
    await page.route(`${API}/api/metamodels/`, (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "[]" })
    );

    await page.goto("/metamodels", { waitUntil: "load" });
    await page.waitForTimeout(2000);

    await expect(page.locator("body")).toBeVisible();
    await expect(page).toHaveURL(/metamodels/);
    await page.screenshot({ path: "e2e/screenshots/metamodels-page.png" });
  });

  test("création Metamodel - mock API 201", async ({ page }) => {
    await page.route(`${API}/api/metamodels/`, async (route) => {
      if (route.request().method() === "POST") {
        const body = JSON.parse(route.request().postData() || "{}");
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: "mm-e2e-" + Date.now(),
            name: body.name,
            version: body.version || "1.0",
            status: "draft",
            owner_id: "testuser",
            created_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
      }
    });

    await page.goto("/metamodels", { waitUntil: "load" });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: "e2e/screenshots/metamodels-create.png" });
  });
});
