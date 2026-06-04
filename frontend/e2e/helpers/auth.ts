import { Page, request } from "@playwright/test";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

let cachedToken: string | null = null;

async function getToken(): Promise<string> {
  if (cachedToken) return cachedToken;
  const ctx = await request.newContext({ baseURL: BACKEND_URL });
  const resp = await ctx.post("/api/auth/dev-login");
  if (!resp.ok()) {
    throw new Error(`dev-login failed: ${resp.status()} ${await resp.text()}`);
  }
  const body = await resp.json();
  cachedToken = body.access_token;
  return cachedToken;
}

/**
 * Log in a test user and set the JWT in localStorage before navigation.
 * Must be called in each test that needs authentication.
 */
export async function loginAsTestUser(page: Page): Promise<string> {
  const token = await getToken();

  // Set token in localStorage before any page JS runs
  await page.addInitScript((t: string) => {
    localStorage.setItem("token", t);
  }, token);

  return token;
}
