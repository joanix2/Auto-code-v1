import { test, expect } from "@playwright/test";
import { loginAsTestUser } from "./helpers/auth";

test.describe("Authentication", () => {

  test("login page shows GitHub auth button", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("Continue with GitHub")).toBeVisible();
  });

  test("GitHub button redirects to GitHub OAuth", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await page.getByText("Continue with GitHub").click();
    const url = page.url();
    expect(url).toContain("github.com/login");
    expect(url).toContain("client_id=");
    expect(decodeURIComponent(url)).toContain("redirect_uri=");
    expect(decodeURIComponent(url)).toContain("state=");
    expect(decodeURIComponent(url)).toContain("localhost");
  });

  test("protected routes redirect to /login when unauthenticated", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    expect(page.url()).toContain("/login");
  });

  test("protected routes redirect to /login for unknown paths", async ({ page }) => {
    await page.goto("/development/projects");
    await page.waitForLoadState("networkidle");
    expect(page.url()).toContain("/login");
  });

  test("dev-login POST returns valid token", async ({ request }) => {
    const resp = await request.post("http://localhost:8000/api/auth/dev-login");
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body).toHaveProperty("access_token");
    expect(body).toHaveProperty("token_type", "bearer");
    expect(body).toHaveProperty("user_id");
    expect(typeof body.access_token).toBe("string");
    expect(body.access_token.split(".").length).toBe(3);
  });

  test("token from dev-login can access /api/auth/me", async ({ request }) => {
    const loginResp = await request.post("http://localhost:8000/api/auth/dev-login");
    const { access_token } = await loginResp.json();

    const meResp = await request.get("http://localhost:8000/api/auth/me", {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    expect(meResp.ok()).toBeTruthy();
    const user = await meResp.json();
    expect(user).toHaveProperty("username", "e2e-test-user");
    expect(user).toHaveProperty("is_active", true);
    expect(user).toHaveProperty("github_token", false);
  });

  test("invalid token is rejected by /api/auth/me", async ({ request }) => {
    const meResp = await request.get("http://localhost:8000/api/auth/me", {
      headers: { Authorization: "Bearer invalid-token" },
    });
    expect(meResp.status()).toBe(401);
  });

  test("missing token is rejected by /api/auth/me", async ({ request }) => {
    const meResp = await request.get("http://localhost:8000/api/auth/me");
    expect(meResp.status()).toBe(403);
  });

  test("authenticated user can access protected pages", async ({ page }) => {
    await loginAsTestUser(page);
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    expect(page.url()).toBe("http://localhost:3000/");
    await expect(page.getByText("Continue with GitHub")).not.toBeVisible();
  });

  test("login page redirects to / when already authenticated", async ({ page }) => {
    await loginAsTestUser(page);
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    expect(page.url()).toBe("http://localhost:3000/");
  });

});
