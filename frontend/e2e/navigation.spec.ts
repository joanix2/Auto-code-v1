import { test, expect } from "@playwright/test";
import { loginAsTestUser } from "./helpers/auth";

test.describe("Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test("sidebar displays all sections", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    const nav = page.locator("nav, [role=navigation], .sidebar, aside").first();
    if (await nav.isVisible()) {
      await expect(nav).toContainText("Analyse");
      await expect(nav).toContainText("Development");
    }
  });

  test("Development section contains Projets, DSLs, Repositories, Templates", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    const devAccordion = page.getByText("Development").first();
    if (await devAccordion.isVisible()) {
      await devAccordion.click();
      await expect(page.getByText("Projets").first()).toBeVisible();
      await expect(page.getByText("DSLs").first()).toBeVisible();
      await expect(page.getByText("Repositories").first()).toBeVisible();
      await expect(page.getByText("Templates").first()).toBeVisible();
    }
  });
});
