import { test, expect, request } from "@playwright/test";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

test.describe("Graph API E2E", () => {
  let ctx: { post: Function; get: Function; delete: Function };

  test.beforeAll(async () => {
    const ctxRaw = await request.newContext({ baseURL: BACKEND });
    ctx = {
      post: (url: string, data?: any) => ctxRaw.post(url, { data }),
      get: (url: string) => ctxRaw.get(url),
      delete: (url: string) => ctxRaw.delete(url),
    };
  });

  test("1. Creer un language", async () => {
    const resp = await ctx.post("/api/languages", { name: "e2e-test", description: "E2E test language" });
    expect(resp.ok()).toBeTruthy();
    const lang = await resp.json();
    expect(lang.name).toBe("e2e-test");
    expect(lang.id).toBeTruthy();
  });

  test("2. Lister les languages", async () => {
    const resp = await ctx.get("/api/languages");
    expect(resp.ok()).toBeTruthy();
    const langs = await resp.json();
    expect(langs.length).toBeGreaterThanOrEqual(1);
    expect(langs.some((l: any) => l.name === "e2e-test")).toBeTruthy();
  });

  test("3. Ajouter des sorts", async () => {
    // Trouver le language e2e-test
    const langs = await (await ctx.get("/api/languages")).json();
    const lang = langs.find((l: any) => l.name === "e2e-test");
    expect(lang).toBeTruthy();

    for (const sort of ["string", "int", "bool", "date"]) {
      const resp = await ctx.post(`/api/languages/${lang.id}/sorts`, { name: sort });
      expect(resp.ok()).toBeTruthy();
      const data = await resp.json();
      expect(data.name).toBe(sort);
      expect(data.kind).toBe("Sort");
    }

    const sorts = await (await ctx.get(`/api/languages/${lang.id}/sorts`)).json();
    expect(sorts.length).toBe(4);
  });

  test("4. Ajouter des ops", async () => {
    const langs = await (await ctx.get("/api/languages")).json();
    const lang = langs.find((l: any) => l.name === "e2e-test");
    expect(lang).toBeTruthy();

    const resp = await ctx.post(`/api/languages/${lang.id}/ops`, {
      name: "Ticket",
      result_sort: "string",
      params: ["string", "int"],
    });
    expect(resp.ok()).toBeTruthy();
    const op = await resp.json();
    expect(op.name).toBe("Ticket");
    expect(op.kind).toBe("Op");

    const ops = await (await ctx.get(`/api/languages/${lang.id}/ops`)).json();
    expect(ops.length).toBe(1);
  });

  test("5. Ajouter equation, regle et invariant", async () => {
    const langs = await (await ctx.get("/api/languages")).json();
    const lang = langs.find((l: any) => l.name === "e2e-test");
    expect(lang).toBeTruthy();

    // Equation
    const eq = await ctx.post(`/api/languages/${lang.id}/equations`, {
      name: "simplify", lhs: "a+0", rhs: "a",
    });
    expect(eq.ok()).toBeTruthy();

    // Rule
    const rl = await ctx.post(`/api/languages/${lang.id}/rules`, {
      name: "dedup", lhs: "T(a)+T(a)", rhs: "T(a)",
    });
    expect(rl.ok()).toBeTruthy();

    // Invariant
    const inv = await ctx.post(`/api/languages/${lang.id}/invariants`, {
      name: "not_null", condition: "x != null",
    });
    expect(inv.ok()).toBeTruthy();

    const eqs = await (await ctx.get(`/api/languages/${lang.id}/equations`)).json();
    expect(eqs.length).toBe(1);

    const rules = await (await ctx.get(`/api/languages/${lang.id}/rules`)).json();
    expect(rules.length).toBe(1);

    const invs = await (await ctx.get(`/api/languages/${lang.id}/invariants`)).json();
    expect(invs.length).toBe(1);
  });

  test("6. Le graphe contient tous les noeuds et aretes", async () => {
    const langs = await (await ctx.get("/api/languages")).json();
    const lang = langs.find((l: any) => l.name === "e2e-test");
    expect(lang).toBeTruthy();

    const graph = await (await ctx.get(`/api/languages/${lang.id}/graph`)).json();
    expect(graph.nodes.length).toBe(8); // 4 sorts + 1 op + 1 equation + 1 rule + 1 invariant

    const kinds = graph.nodes.map((n: any) => n.kind);
    expect(kinds.filter((k: string) => k === "Sort").length).toBe(4);
    expect(kinds.filter((k: string) => k === "Op").length).toBe(1);
    expect(kinds.filter((k: string) => k === "Equation").length).toBe(1);
    expect(kinds.filter((k: string) => k === "Rule").length).toBe(1);
    expect(kinds.filter((k: string) => k === "Invariant").length).toBe(1);

    // Verifier les aretes
    expect(graph.edges.length).toBeGreaterThan(0);
    const edgeKinds = graph.edges.map((e: any) => e.kind);
    expect(edgeKinds).toContain("has_sort");
    expect(edgeKinds).toContain("has_param");
  });

  test("7. Supprimer le language de test", async () => {
    const langs = await (await ctx.get("/api/languages")).json();
    const lang = langs.find((l: any) => l.name === "e2e-test");
    if (lang) {
      const resp = await ctx.delete(`/api/languages/${lang.id}`);
      expect(resp.ok()).toBeTruthy();
    }
  });
});
