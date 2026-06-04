import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useDsl } from "./useDsl";
import { dslService } from "../services/dslService";

vi.mock("../services/dslService", () => ({
  dslService: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    validate: vi.fn(),
    deprecate: vi.fn(),
  },
}));

const mockDsl = {
  id: "1",
  name: "Test DSL",
  version: "1.0",
  node_count: 0,
  edge_count: 0,
  created_at: "2024-01-01T00:00:00Z",
  status: "draft" as const,
};

describe("useDsl", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches DSls on mount", async () => {
    vi.mocked(dslService.getAll).mockResolvedValue([mockDsl]);
    const { result } = renderHook(() => useDsl());
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.dsls).toEqual([mockDsl]);
    expect(result.current.error).toBeNull();
  });

  it("handles fetch error", async () => {
    vi.mocked(dslService.getAll).mockRejectedValue(new Error("Network error"));
    const { result } = renderHook(() => useDsl());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.dsls).toEqual([]);
    expect(result.current.error).toBe("Network error");
  });

  it("creates a DSL", async () => {
    vi.mocked(dslService.getAll).mockResolvedValue([]);
    vi.mocked(dslService.create).mockResolvedValue(mockDsl);
    const { result } = renderHook(() => useDsl());
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      const created = await result.current.createDSLGraph({ name: "Test DSL", version: "1.0" });
      expect(created).toEqual(mockDsl);
    });
    expect(result.current.dsls).toContainEqual(mockDsl);
  });

  it("updates a DSL", async () => {
    const updated = { ...mockDsl, name: "Updated" };
    vi.mocked(dslService.getAll).mockResolvedValue([mockDsl]);
    vi.mocked(dslService.update).mockResolvedValue(updated);
    const { result } = renderHook(() => useDsl());
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      const res = await result.current.updateDSLGraph("1", { name: "Updated" });
      expect(res).toEqual(updated);
    });
    expect(result.current.dsls[0].name).toBe("Updated");
  });

  it("deletes a DSL", async () => {
    vi.mocked(dslService.getAll).mockResolvedValue([mockDsl]);
    vi.mocked(dslService.delete).mockResolvedValue(undefined);
    const { result } = renderHook(() => useDsl());
    await waitFor(() => { expect(result.current.loading).toBe(false); expect(result.current.dsls).toHaveLength(1); });
    await act(async () => { await result.current.deleteDSLGraph("1"); });
    expect(result.current.dsls).toHaveLength(0);
  });

  it("validates a DSL", async () => {
    const validated = { ...mockDsl, status: "validated" as const };
    vi.mocked(dslService.getAll).mockResolvedValue([mockDsl]);
    vi.mocked(dslService.validate).mockResolvedValue(validated);
    const { result } = renderHook(() => useDsl());
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      const res = await result.current.validateDSLGraph("1");
      expect(res.status).toBe("validated");
    });
    expect(result.current.dsls[0].status).toBe("validated");
  });

  it("deprecates a DSL", async () => {
    const deprecated = { ...mockDsl, status: "deprecated" as const };
    vi.mocked(dslService.getAll).mockResolvedValue([mockDsl]);
    vi.mocked(dslService.deprecate).mockResolvedValue(deprecated);
    const { result } = renderHook(() => useDsl());
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(async () => {
      const res = await result.current.deprecateDSLGraph("1");
      expect(res.status).toBe("deprecated");
    });
    expect(result.current.dsls[0].status).toBe("deprecated");
  });

  it("refetch reloads DSLs", async () => {
    vi.mocked(dslService.getAll).mockResolvedValueOnce([mockDsl]);
    vi.mocked(dslService.getAll).mockResolvedValueOnce([]);
    const { result } = renderHook(() => useDsl());
    await waitFor(() => expect(result.current.dsls).toHaveLength(1));
    await act(async () => { await result.current.refetch(); });
    expect(result.current.dsls).toHaveLength(0);
  });
});
