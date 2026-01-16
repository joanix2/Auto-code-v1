/**
 * Concept Service - API calls for MDE concepts
 */
import { BaseService } from "./base.service";
import { apiService } from "./api.service";

export interface Concept {
  id: string;
  name: string;
  description?: string;
  graph_id: string;
  x_position?: number;
  y_position?: number;
  created_at: string;
  updated_at?: string;
}

export interface ConceptCreate {
  name: string;
  description?: string;
  graph_id: string;
  x_position?: number;
  y_position?: number;
}

export type ConceptUpdate = Partial<ConceptCreate>;

interface Attribute {
  id: string;
  name: string;
  type: string;
  [key: string]: unknown;
}

class ConceptService extends BaseService<Concept, ConceptCreate, ConceptUpdate> {
  protected basePath = "/api/concepts";

  /**
   * Get all concepts for a metamodel
   */
  async getByMetamodel(metamodelId: string): Promise<Concept[]> {
    return apiService.get<Concept[]>(this.basePath, {
      params: { metamodel_id: metamodelId },
    });
  }

  /**
   * Get concept with its attributes
   */
  async getWithAttributes(id: string): Promise<Concept & { attributes: Attribute[] }> {
    return apiService.get<Concept & { attributes: Attribute[] }>(`${this.basePath}/${id}/with-attributes`);
  }

  /**
   * Update concept position in graph
   */
  async updatePosition(id: string, x: number, y: number): Promise<Concept> {
    return apiService.patch<Concept>(`${this.basePath}/${id}/position`, null, {
      params: { x, y },
    });
  }
}

export const conceptService = new ConceptService();
export default conceptService;
