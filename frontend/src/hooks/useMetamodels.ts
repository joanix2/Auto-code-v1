import { useState, useEffect } from "react";
import { Metamodel, MetamodelCreate, MetamodelUpdate } from "@/types/metamodel";
import { metamodelService } from "../services/metamodelService";

export function useMetamodels() {
  const [metamodels, setMetamodels] = useState<Metamodel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetamodels = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await metamodelService.getAll();
      setMetamodels(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch metamodels");
      console.error("Error fetching metamodels:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetamodels();
  }, []);

  const createMetamodel = async (data: MetamodelCreate) => {
    try {
      const newMetamodel = await metamodelService.create(data);
      setMetamodels((prev) => [...prev, newMetamodel]);
      return newMetamodel;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create metamodel");
      throw err;
    }
  };

  const updateMetamodel = async (id: string, data: MetamodelUpdate) => {
    try {
      const updated = await metamodelService.update(id, data);
      setMetamodels((prev) => prev.map((m) => (m.id === id ? updated : m)));
      return updated;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update metamodel");
      throw err;
    }
  };

  const deleteMetamodel = async (id: string) => {
    try {
      await metamodelService.delete(id);
      setMetamodels((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete metamodel");
      throw err;
    }
  };

  const validateMetamodel = async (id: string) => {
    try {
      const validated = await metamodelService.validate(id);
      setMetamodels((prev) => prev.map((m) => (m.id === id ? validated : m)));
      return validated;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to validate metamodel");
      throw err;
    }
  };

  const deprecateMetamodel = async (id: string) => {
    try {
      const deprecated = await metamodelService.deprecate(id);
      setMetamodels((prev) => prev.map((m) => (m.id === id ? deprecated : m)));
      return deprecated;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to deprecate metamodel");
      throw err;
    }
  };

  return {
    metamodels,
    loading,
    error,
    refetch: fetchMetamodels,
    createMetamodel,
    updateMetamodel,
    deleteMetamodel,
    validateMetamodel,
    deprecateMetamodel,
  };
}
