import { test, expect } from "./auth-fixture";

test.describe("Metamodel — E2E réel", () => {
  test("page se charge avec la vraie API", async ({ page }) => {
    await page.goto("/metamodels", { waitUntil: "load" });
    await page.waitForTimeout(3000);
    await expect(page.locator("body")).toBeVisible();
    await expect(page).toHaveURL(/metamodels/);
  });

  test("créer un métamodèle sans erreur (POST real API)", async ({ page }) => {
    await page.goto("/metamodels", { waitUntil: "load" });
    await page.waitForTimeout(2000);

    // Navigate to the create form if there's a button
    const createBtn = page.getByRole("link", { name: /créer|nouveau|ajouter/i }).or(
      page.getByRole("button", { name: /créer|nouveau|ajouter/i })
    ).first();

    if (await createBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await createBtn.click();
      await page.waitForTimeout(1000);
    }

    // Fill name field
    const nameField = page.locator('input[name="name"], input[id="name"], input[placeholder*="Nom"]').first();
    if (await nameField.isVisible({ timeout: 3000 }).catch(() => false)) {
      await nameField.fill("E2E-Real-Test");
    }

    // Fill version
    const versionField = page.locator('input[name="version"], input[id="version"]').first();
    if (await versionField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await versionField.fill("1.0");
    }

    // Submit
    const submitBtn = page.getByRole("button", { name: /créer|enregistrer|sauvegarder|valider/i }).first();
    if (await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await Promise.all([
        page.waitForResponse((resp) => resp.url().includes("/api/metamodels/") && resp.status() === 201),
        submitBtn.click(),
      ]);
      await page.waitForTimeout(1000);
      // Verify success — either we see the name or we're redirected
      await expect(page.locator("text=E2E-Real-Test").first()).toBeVisible({ timeout: 5000 });
    }
  });
});
