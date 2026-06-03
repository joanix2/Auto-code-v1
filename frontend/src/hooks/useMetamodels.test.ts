import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useMetamodels } from "./useMetamodels";
import { metamodelService } from "../services/metamodelService";

vi.mock("../services/metamodelService", () => ({
  metamodelService: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    validate: vi.fn(),
    deprecate: vi.fn(),
  },
}));

const mockMetamodel = {
  id: "1",
  name: "Test Metamodel",
  version: "1.0",
  node_count: 0,
  edge_count: 0,
  created_at: "2024-01-01T00:00:00Z",
  status: "draft" as const,
};

describe("useMetamodels", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches metamodels on mount", async () => {
    vi.mocked(metamodelService.getAll).mockResolvedValue([mockMetamodel]);

    const { result } = renderHook(() => useMetamodels());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.metamodels).toEqual([mockMetamodel]);
    expect(result.current.error).toBeNull();
  });

  it("handles fetch error", async () => {
    vi.mocked(metamodelService.getAll).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useMetamodels());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.metamodels).toEqual([]);
    expect(result.current.error).toBe("Network error");
  });

  it("creates a metamodel", async () => {
    vi.mocked(metamodelService.getAll).mockResolvedValue([]);
    vi.mocked(metamodelService.create).mockResolvedValue(mockMetamodel);

    const { result } = renderHook(() => useMetamodels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      const created = await result.current.createMetamodel({
        name: "Test Metamodel",
        version: "1.0",
      });
      expect(created).toEqual(mockMetamodel);
    });

    expect(result.current.metamodels).toContainEqual(mockMetamodel);
  });

  it("updates a metamodel", async () => {
    const updated = { ...mockMetamodel, name: "Updated" };
    vi.mocked(metamodelService.getAll).mockResolvedValue([mockMetamodel]);
    vi.mocked(metamodelService.update).mockResolvedValue(updated);

    const { result } = renderHook(() => useMetamodels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      const res = await result.current.updateMetamodel("1", { name: "Updated" });
      expect(res).toEqual(updated);
    });

    expect(result.current.metamodels[0].name).toBe("Updated");
  });

  it("deletes a metamodel", async () => {
    vi.mocked(metamodelService.getAll).mockResolvedValue([mockMetamodel]);
    vi.mocked(metamodelService.delete).mockResolvedValue(undefined);

    const { result } = renderHook(() => useMetamodels());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.metamodels).toHaveLength(1);

    await act(async () => {
      await result.current.deleteMetamodel("1");
    });

    expect(result.current.metamodels).toHaveLength(0);
  });

  it("validates a metamodel", async () => {
    const validated = { ...mockMetamodel, status: "validated" as const };
    vi.mocked(metamodelService.getAll).mockResolvedValue([mockMetamodel]);
    vi.mocked(metamodelService.validate).mockResolvedValue(validated);

    const { result } = renderHook(() => useMetamodels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      const res = await result.current.validateMetamodel("1");
      expect(res.status).toBe("validated");
    });

    expect(result.current.metamodels[0].status).toBe("validated");
  });

  it("deprecates a metamodel", async () => {
    const deprecated = { ...mockMetamodel, status: "deprecated" as const };
    vi.mocked(metamodelService.getAll).mockResolvedValue([mockMetamodel]);
    vi.mocked(metamodelService.deprecate).mockResolvedValue(deprecated);

    const { result } = renderHook(() => useMetamodels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      const res = await result.current.deprecateMetamodel("1");
      expect(res.status).toBe("deprecated");
    });

    expect(result.current.metamodels[0].status).toBe("deprecated");
  });

  it("refetch reloads metamodels", async () => {
    vi.mocked(metamodelService.getAll).mockResolvedValueOnce([mockMetamodel]);
    vi.mocked(metamodelService.getAll).mockResolvedValueOnce([]);

    const { result } = renderHook(() => useMetamodels());

    await waitFor(() => expect(result.current.metamodels).toHaveLength(1));

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.metamodels).toHaveLength(0);
  });
});
