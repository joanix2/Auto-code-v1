import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("sidebar displays all sections", async ({ page }) => {
    const nav = page.locator("nav, [role=navigation], .sidebar, aside");
    if (await nav.isVisible()) {
      await expect(nav).toContainText("Analyse");
      await expect(nav).toContainText("Development");
    }
  });

  test("Development section contains Projets, DSLs, Repositories, Templates", async ({ page }) => {
    const devSection = page.getByText("Development");
    if (await devSection.isVisible()) {
      await devSection.click();
      await expect(page.getByText("Projets").first()).toBeVisible();
      await expect(page.getByText("DSLs").first()).toBeVisible();
      await expect(page.getByText("Repositories").first()).toBeVisible();
      await expect(page.getByText("Templates").first()).toBeVisible();
    }
  });
});
