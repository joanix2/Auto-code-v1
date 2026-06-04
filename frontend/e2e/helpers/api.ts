import { request, APIRequestContext } from "@playwright/test";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

let apiContext: APIRequestContext | null = null;
let authToken: string | null = null;

async function ensureAuth(): Promise<string> {
  if (authToken) return authToken;
  const ctx = await request.newContext({ baseURL: BACKEND_URL });
  const resp = await ctx.post("/api/auth/dev-login");
  if (!resp.ok()) {
    throw new Error(`Auth failed: ${resp.status()} ${await resp.text()}`);
  }
  const body = await resp.json();
  authToken = body.access_token;
  return authToken!;
}

export async function getApiContext(): Promise<APIRequestContext> {
  if (!apiContext) {
    const token = await ensureAuth();
    apiContext = await request.newContext({
      baseURL: BACKEND_URL,
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });
  }
  return apiContext;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const ctx = await request.newContext({ baseURL: BACKEND_URL });
    const resp = await ctx.get("/health", { timeout: 5000 });
    return resp.ok();
  } catch {
    return false;
  }
}

export async function waitForBackend(maxRetries = 10, delayMs = 2000): Promise<void> {
  for (let i = 0; i < maxRetries; i++) {
    const ok = await healthCheck();
    if (ok) return;
    console.log(`Waiting for backend... attempt ${i + 1}/${maxRetries}`);
    await new Promise((r) => setTimeout(r, delayMs));
  }
  throw new Error("Backend not ready after max retries");
}

export async function createProject(name: string, description?: string) {
  const ctx = await getApiContext();
  const resp = await ctx.post("/api/projects", {
    data: { name, description },
  });
  if (!resp.ok()) {
    throw new Error(`Failed to create project: ${resp.status()} ${await resp.text()}`);
  }
  return resp.json();
}

export async function deleteProject(id: string) {
  const ctx = await getApiContext();
  const resp = await ctx.delete(`/api/projects/${id}`);
  if (!resp.ok()) {
    throw new Error(`Failed to delete project ${id}: ${resp.status()}`);
  }
}

export async function getProjects(): Promise<any[]> {
  const ctx = await getApiContext();
  const resp = await ctx.get("/api/projects");
  if (!resp.ok()) return [];
  return resp.json();
}

export async function cleanupProjects(keepIds: string[] = []) {
  const projects = await getProjects();
  for (const p of projects) {
    if (!keepIds.includes(p.id)) {
      await deleteProject(p.id).catch(() => {});
    }
  }
}
