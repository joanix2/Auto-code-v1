import { useState, useEffect } from "react";
import { DSLGraph, DSLGraphCreate, DSLGraphUpdate } from "@/types/dsl";
import { dslService } from "../services/dslService";

export function useDsl() {
  const [dsls, setDSLGraphs] = useState<DSLGraph[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDSLGraphs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dslService.getAll();
      setDSLGraphs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch dsls");
      console.error("Error fetching dsls:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDSLGraphs();
  }, []);

  const createDSLGraph = async (data: DSLGraphCreate) => {
    try {
      const newDSLGraph = await dslService.create(data);
      setDSLGraphs((prev) => [...prev, newDSLGraph]);
      return newDSLGraph;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create dsl");
      throw err;
    }
  };

  const updateDSLGraph = async (id: string, data: DSLGraphUpdate) => {
    try {
      const updated = await dslService.update(id, data);
      setDSLGraphs((prev) => prev.map((m) => (m.id === id ? updated : m)));
      return updated;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update dsl");
      throw err;
    }
  };

  const deleteDSLGraph = async (id: string) => {
    try {
      await dslService.delete(id);
      setDSLGraphs((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete dsl");
      throw err;
    }
  };

  const validateDSLGraph = async (id: string) => {
    try {
      const validated = await dslService.validate(id);
      setDSLGraphs((prev) => prev.map((m) => (m.id === id ? validated : m)));
      return validated;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to validate dsl");
      throw err;
    }
  };

  const deprecateDSLGraph = async (id: string) => {
    try {
      const deprecated = await dslService.deprecate(id);
      setDSLGraphs((prev) => prev.map((m) => (m.id === id ? deprecated : m)));
      return deprecated;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to deprecate dsl");
      throw err;
    }
  };

  return {
    dsls,
    loading,
    error,
    refetch: fetchDSLGraphs,
    createDSLGraph,
    updateDSLGraph,
    deleteDSLGraph,
    validateDSLGraph,
    deprecateDSLGraph,
  };
}
