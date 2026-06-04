import { BaseService } from "./base.service";
import { DSLGraph, DSLGraphCreate, DSLGraphUpdate } from "@/types/dsl";
import { apiService } from "./api.service";
import { M3EdgeType } from "@/types/dsl-config";

// Re-export for convenience
export type { M3EdgeType } from "@/types/dsl-config";

class DSLService extends BaseService<DSLGraph, DSLGraphCreate, DSLGraphUpdate> {
  protected basePath = "/api/dsls";

  /**
   * Get dsls by status
   */
  async getByStatus(status: string): Promise<DSLGraph[]> {
    return apiService.get<DSLGraph[]>(this.basePath, { params: { status } });
  }

  /**
   * Get dsls by author
   */
  async getByAuthor(author: string): Promise<DSLGraph[]> {
    return apiService.get<DSLGraph[]>(this.basePath, { params: { author } });
  }

  /**
   * Validate a dsl (change status to validated)
   */
  async validate(id: string): Promise<DSLGraph> {
    return apiService.post<DSLGraph>(`${this.basePath}/${id}/validate`);
  }

  /**
   * Deprecate a dsl (change status to deprecated)
   */
  async deprecate(id: string): Promise<DSLGraph> {
    return apiService.post<DSLGraph>(`${this.basePath}/${id}/deprecate`);
  }

  /**
   * Get complete dsl graph with all nodes and edges
   */
  async getGraph(id: string): Promise<{
    dsl: DSLGraph; // Objet DSLGraph complet
    nodes: Array<{
      id: string;
      name: string;
      description?: string;
      type: string;
      label: string;
      x?: number;
      y?: number;
      created_at: string;
      updated_at?: string;
      // Propriétés spécifiques aux Attributes
      dataType?: string; // Type de données (string, integer, etc.)
      isRequired?: boolean; // Attribut requis
      isUnique?: boolean; // Valeur unique
      concept_id?: string; // ID du concept parent
      // Propriétés spécifiques aux Relations
      relationType?: string; // Type de relation (is_a, has_part, etc.)
    }>;
    edges: Array<{
      id: string;
      description?: string;
      type: string;
      label: string;
      source: string;
      target: string;
      source_label?: string;
      target_label?: string;
      directed: boolean;
      created_at: string;
      updated_at?: string;
    }>;
    edgeConstraints: M3EdgeType[]; // Edge type constraints from M3
  }> {
    return apiService.get(`${this.basePath}/${id}/graph`);
  }
}

export const dslService = new DSLService();
