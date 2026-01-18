/**
 * Relationship Service - API calls for MDE relationships
 */
import { BaseService } from "./base.service";
import { apiService } from "./api.service";

export interface Relationship {
  id: string;
  name: string; // Nom de la relation (obligatoire)
  type: "is_a" | "has_part" | "has_subclass" | "part_of" | "other";
  description?: string;
  graph_id: string; // ID du metamodel parent
  x_position?: number;
  y_position?: number;
  created_at: string;
  updated_at?: string;
}

export interface RelationshipCreate {
  name: string; // Nom de la relation (obligatoire)
  type: "is_a" | "has_part" | "has_subclass" | "part_of" | "other";
  description?: string;
  graph_id: string; // ID du metamodel parent
  x_position?: number;
  y_position?: number;
}

export type RelationshipUpdate = Partial<Omit<RelationshipCreate, "graph_id">>;

class RelationshipService extends BaseService<Relationship, RelationshipCreate, RelationshipUpdate> {
  protected basePath = "/api/relationships";

  /**
   * Get all relationships for a metamodel
   */
  async getByMetamodel(metamodelId: string, includeInverse: boolean = true): Promise<Relationship[]> {
    return apiService.get<Relationship[]>(`${this.basePath}/metamodel/${metamodelId}?include_inverse=${includeInverse}`);
  }

  /**
   * Get all relationships for a concept
   */
  async getByConcept(conceptId: string, direction: "outgoing" | "incoming" | "both" = "both"): Promise<{ outgoing: Relationship[]; incoming: Relationship[] }> {
    return apiService.get<{ outgoing: Relationship[]; incoming: Relationship[] }>(`${this.basePath}/concept/${conceptId}?direction=${direction}`);
  }

  /**
   * Infer new relationships using ontological reasoning
   */
  async inferRelationships(metamodelId: string): Promise<{ count: number; relationships: Relationship[]; message: string }> {
    return apiService.post<{ count: number; relationships: Relationship[]; message: string }>(`${this.basePath}/metamodel/${metamodelId}/infer`, {});
  }
}

export const relationshipService = new RelationshipService();
