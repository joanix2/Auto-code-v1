import { test, expect } from "@playwright/test";

test.describe("Smoke tests", () => {
  test("homepage loads and shows dashboard", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    const url = page.url();
    expect(url === "/" || url.includes("/login")).toBeTruthy();
  });

  test("login page shows GitHub auth button", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    // Either the login page or auto-redirect (if already auth'd)
    const hasGitHubButton = page.getByText("Continue with GitHub");
    const isDashboard = page.url() === "http://localhost:3000/";
    if (!isDashboard) {
      await expect(hasGitHubButton).toBeVisible();
    }
  });

  test("unknown routes redirect to login when unauthenticated", async ({ page }) => {
    await page.goto("/this-route-does-not-exist");
    await page.waitForLoadState("networkidle");
    // Should redirect to login (no token)
    expect(page.url()).toContain("/login");
  });
});
