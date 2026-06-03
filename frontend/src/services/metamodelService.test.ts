import { describe, it, expect, vi, beforeEach } from "vitest";
import { metamodelService } from "./metamodelService";
import { apiService } from "./api.service";

vi.mock("./api.service", () => ({
  apiService: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe("MetamodelService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getAll", () => {
    it("calls apiService.get with correct path", async () => {
      vi.mocked(apiService.get).mockResolvedValue([]);

      await metamodelService.getAll();

      expect(apiService.get).toHaveBeenCalledWith("/api/metamodels", { params: undefined });
    });

    it("returns metamodels list", async () => {
      const mockMetamodels = [
        { id: "1", name: "Test", version: "1.0", node_count: 0, edge_count: 0, created_at: "2024-01-01" },
      ];
      vi.mocked(apiService.get).mockResolvedValue(mockMetamodels);

      const result = await metamodelService.getAll();

      expect(result).toEqual(mockMetamodels);
    });
  });

  describe("getById", () => {
    it("calls apiService.get with correct id", async () => {
      vi.mocked(apiService.get).mockResolvedValue({ id: "1", name: "Test" });

      await metamodelService.getById("1");

      expect(apiService.get).toHaveBeenCalledWith("/api/metamodels/1");
    });
  });

  describe("create", () => {
    it("sends POST request with data", async () => {
      const createData = { name: "New Metamodel", version: "1.0" };
      vi.mocked(apiService.post).mockResolvedValue({ id: "1", ...createData });

      await metamodelService.create(createData);

      expect(apiService.post).toHaveBeenCalledWith("/api/metamodels", createData);
    });
  });

  describe("update", () => {
    it("sends PUT request with id and data", async () => {
      const updateData = { name: "Updated" };
      vi.mocked(apiService.put).mockResolvedValue({ id: "1", ...updateData });

      await metamodelService.update("1", updateData);

      expect(apiService.put).toHaveBeenCalledWith("/api/metamodels/1", updateData);
    });
  });

  describe("delete", () => {
    it("sends DELETE request with id", async () => {
      vi.mocked(apiService.delete).mockResolvedValue(undefined);

      await metamodelService.delete("1");

      expect(apiService.delete).toHaveBeenCalledWith("/api/metamodels/1");
    });
  });

  describe("getByStatus", () => {
    it("calls with status query param", async () => {
      vi.mocked(apiService.get).mockResolvedValue([]);

      await metamodelService.getByStatus("draft");

      expect(apiService.get).toHaveBeenCalledWith("/api/metamodels", {
        params: { status: "draft" },
      });
    });
  });

  describe("getByAuthor", () => {
    it("calls with author query param", async () => {
      vi.mocked(apiService.get).mockResolvedValue([]);

      await metamodelService.getByAuthor("john");

      expect(apiService.get).toHaveBeenCalledWith("/api/metamodels", {
        params: { author: "john" },
      });
    });
  });

  describe("validate", () => {
    it("sends POST to validate endpoint", async () => {
      vi.mocked(apiService.post).mockResolvedValue({ id: "1", status: "validated" });

      const result = await metamodelService.validate("1");

      expect(apiService.post).toHaveBeenCalledWith("/api/metamodels/1/validate");
      expect(result.status).toBe("validated");
    });
  });

  describe("deprecate", () => {
    it("sends POST to deprecate endpoint", async () => {
      vi.mocked(apiService.post).mockResolvedValue({ id: "1", status: "deprecated" });

      const result = await metamodelService.deprecate("1");

      expect(apiService.post).toHaveBeenCalledWith("/api/metamodels/1/deprecate");
      expect(result.status).toBe("deprecated");
    });
  });

  describe("getGraph", () => {
    it("returns graph data structure", async () => {
      const mockGraph = {
        metamodel: { id: "1", name: "Test", version: "1.0", node_count: 0, edge_count: 0, created_at: "2024-01-01" },
        nodes: [],
        edges: [],
        edgeConstraints: [],
      };
      vi.mocked(apiService.get).mockResolvedValue(mockGraph);

      const result = await metamodelService.getGraph("1");

      expect(apiService.get).toHaveBeenCalledWith("/api/metamodels/1/graph");
      expect(result).toEqual(mockGraph);
    });
  });
});
