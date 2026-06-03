import { Page, test as base } from "@playwright/test";

const API = "http://localhost:8000";
const FAKE_TOKEN = "e2e-sso-token";

export type AuthOptions = {
  mockUser?: Record<string, unknown>;
};

export const test = base.extend<{ auth: void }>({
  auth: [
    async ({ page }, use) => {
      // Inject fake JWT into localStorage before any page load
      await page.addInitScript((token) => {
        localStorage.setItem("token", token);
      }, FAKE_TOKEN);

      // Mock the auth/user endpoint to return a valid user
      await mockAuthEndpoint(page);

      await use();
    },
    { auto: true },
  ],
});

export { expect } from "@playwright/test";

/**
 * Mock the /api/auth/me endpoint to return a fake user.
 * This simulates a successful SSO login without needing GitHub OAuth.
 */
export async function mockAuthEndpoint(page: Page, user?: Record<string, unknown>) {
  await page.route(`${API}/api/auth/me`, (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(user ?? {
        id: "user-e2e",
        username: "testuser",
        email: "test@example.com",
        is_active: true,
        avatar_url: "",
        github_token: true,
      }),
    });
  });
}

/**
 * Mock a REST API endpoint with a canned response.
 * Supports GET, POST, PUT, PATCH, DELETE.
 */
export async function mockApi(
  page: Page,
  urlPattern: string | RegExp,
  response: unknown,
  method?: string,
) {
  await page.route(urlPattern, async (route) => {
    if (method && route.request().method() !== method) {
      await route.fallback();
      return;
    }
    const status = method === "POST" ? 201 : 200;
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(response),
    });
  });
}

/**
 * Mock a REST endpoint with a handler function (e.g. to inspect request body).
 */
export async function mockApiHandler(
  page: Page,
  urlPattern: string | RegExp,
  handler: (route: Parameters<Parameters<typeof page.route>[1]>[0]) => void,
) {
  await page.route(urlPattern, handler);
}

/**
 * Mock the metamodels list endpoint and create endpoint.
 */
export async function mockMetamodels(page: Page) {
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
}
