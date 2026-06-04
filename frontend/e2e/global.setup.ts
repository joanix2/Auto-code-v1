import { test as setup, expect } from "@playwright/test";
import { healthCheck, waitForBackend } from "./helpers/api";

setup("backend must be reachable", async () => {
  await waitForBackend();
  const ok = await healthCheck();
  expect(ok).toBeTruthy();
});
