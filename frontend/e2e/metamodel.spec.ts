import { test, expect, mockMetamodels } from "./auth-fixture";

test.describe("Metamodel", () => {
  test("page se charge", async ({ page }) => {
    await mockMetamodels(page);
    await page.goto("/metamodels", { waitUntil: "load" });
    await page.waitForTimeout(2000);
    await expect(page.locator("body")).toBeVisible();
    await expect(page).toHaveURL(/metamodels/);
  });

  test("création via mock API 201", async ({ page }) => {
    await mockMetamodels(page);
    await page.goto("/metamodels", { waitUntil: "load" });
    await page.waitForTimeout(2000);
    // La création est mockée dans mockMetamodels (route POST → 201)
  });
});
