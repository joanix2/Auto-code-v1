/**
 * Attribute Service - API calls for MDE attributes
 */
import { BaseService } from "./base.service";
import { apiService } from "./api.service";

export interface Attribute {
  id: string;
  name: string;
  description?: string;
  graph_id: string;
  concept_id: string;
  type: string; // AttributeType: string, integer, float, boolean, date
  is_required: boolean;
  is_unique: boolean;
  x_position?: number;
  y_position?: number;
  created_at: string;
  updated_at?: string;
}

export interface AttributeCreate {
  name: string;
  description?: string;
  graph_id: string;
  concept_id?: string; // Optional - can be linked to concept later
  type: string;
  is_required?: boolean;
  is_unique?: boolean;
  x_position?: number;
  y_position?: number;
}

export type AttributeUpdate = Partial<Omit<AttributeCreate, "graph_id" | "concept_id">>;

class AttributeService extends BaseService<Attribute, AttributeCreate, AttributeUpdate> {
  protected basePath = "/api/attributes";

  /**
   * Get all attributes for a concept
   */
  async getByConcept(conceptId: string): Promise<Attribute[]> {
    return apiService.get<Attribute[]>(`${this.basePath}/concept/${conceptId}`);
  }

  /**
   * Get all attributes for a metamodel
   */
  async getByMetamodel(metamodelId: string): Promise<Attribute[]> {
    return apiService.get<Attribute[]>(`${this.basePath}/metamodel/${metamodelId}`);
  }

  /**
   * Get required attributes for a concept
   */
  async getRequiredAttributes(conceptId: string): Promise<Attribute[]> {
    const attributes = await this.getByConcept(conceptId);
    return attributes.filter((attr) => attr.is_required);
  }
}

export const attributeService = new AttributeService();
