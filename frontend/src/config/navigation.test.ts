import { describe, it, expect } from "vitest";
import { navigation, NavigationItem } from "./navigation";

function findItem(items: NavigationItem[], name: string): NavigationItem | undefined {
  for (const item of items) {
    if (item.name === name) return item;
    if (item.children) {
      const found = findItem(item.children, name);
      if (found) return found;
    }
  }
  return undefined;
}

describe("Navigation structure", () => {
  it("has 3 top-level sections", () => {
    expect(navigation).toHaveLength(3);
    expect(navigation[0].name).toBe("Home");
    expect(navigation[1].name).toBe("Analyse");
    expect(navigation[2].name).toBe("Development");
  });

  describe("Analyse section", () => {
    const analyse = navigation[1];
    it("has 5 sub-items", () => {
      expect(analyse.children).toHaveLength(5);
    });
    it("includes all expected items", () => {
      const names = analyse.children!.map((c) => c.name);
      expect(names).toContain("Avatars client");
      expect(names).toContain("Besoins");
      expect(names).toContain("Solutions techniques");
      expect(names).toContain("Clients");
      expect(names).toContain("Cartographie");
    });
  });

  describe("Development section", () => {
    const dev = navigation[2];
    it("has 5 sub-items", () => {
      expect(dev.children).toHaveLength(5);
    });

    it("includes Projets as first item and Agent as last", () => {
      const names = dev.children!.map((c) => c.name);
      expect(names[0]).toBe("Projets");
      expect(names[names.length - 1]).toBe("Agent");
    });

    it("includes Projets", () => {
      const projets = findItem(navigation, "Projets");
      expect(projets).toBeDefined();
      expect(projets!.href).toBe("/development/projets");
    });

    it("includes DSLs", () => {
      const dsls = findItem(navigation, "DSLs");
      expect(dsls).toBeDefined();
      expect(dsls!.href).toBe("/development/dsls");
    });

    it("no longer has Modeles in development", () => {
      const modeles = findItem(navigation, "Modeles");
      expect(modeles).toBeUndefined();
    });

    it("includes Templates before Repositories", () => {
      const dev = navigation[2];
      const names = dev.children!.map((c) => c.name);
      const templatesIdx = names.indexOf("Templates");
      const reposIdx = names.indexOf("Repositories");
      expect(templatesIdx).toBeLessThan(reposIdx);
    });

    it("includes Repositories", () => {
      const repos = findItem(navigation, "Repositories");
      expect(repos).toBeDefined();
      expect(repos!.href).toBe("/development/repositories");
    });

    it("includes Templates", () => {
      const templates = findItem(navigation, "Templates");
      expect(templates).toBeDefined();
      expect(templates!.href).toBe("/development/templates");
    });

    it("includes Agent as last item", () => {
      const agent = findItem(navigation, "Agent");
      expect(agent).toBeDefined();
      expect(agent!.href).toBe("/development/agent");
    });
  });

  it("all items have required fields", () => {
    function validate(items: NavigationItem[]) {
      for (const item of items) {
        expect(item.icon).toBeDefined();
        expect(item.name).toBeTruthy();
        if (item.children) {
          expect(item.href).toBeUndefined();
          validate(item.children);
        } else {
          expect(item.href).toBeDefined();
        }
      }
    }
    validate(navigation);
  });
});
