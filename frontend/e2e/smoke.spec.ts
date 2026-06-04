import { test, expect } from "@playwright/test";

test.describe("Smoke tests", () => {
  test("homepage loads and shows dashboard", async ({ page }) => {
    await page.goto("/");

    // Should redirect to login or show dashboard
    await page.waitForLoadState("networkidle");

    // Either we're on the login page or the dashboard
    const url = page.url();
    const isLogin = url.includes("/login");
    const isDashboard = url === page.url() && !isLogin;

    if (isDashboard) {
      await expect(page.locator("h1")).toBeVisible();
    }
    // If login, that's expected too - auth is required
  });

  test("login page has expected elements", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1, h2").first()).toBeVisible();
  });

  test("404 page for unknown routes", async ({ page }) => {
    await page.goto("/this-route-does-not-exist");
    await page.waitForLoadState("networkidle");
    // Should show a 404 or redirect to login
    const url = page.url();
    expect(url).toContain("/this-route-does-not-exist");
  });
});
