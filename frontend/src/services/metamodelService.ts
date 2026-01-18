import { BaseService } from "./base.service";
import { Metamodel, MetamodelCreate, MetamodelUpdate } from "@/types/metamodel";
import { EdgeTypeConstraint } from "@/components/common/GraphViewer";
import { apiService } from "./api.service";

class MetamodelService extends BaseService<Metamodel, MetamodelCreate, MetamodelUpdate> {
  protected basePath = "/api/metamodels";

  /**
   * Get metamodels by status
   */
  async getByStatus(status: string): Promise<Metamodel[]> {
    return apiService.get<Metamodel[]>(this.basePath, { params: { status } });
  }

  /**
   * Get metamodels by author
   */
  async getByAuthor(author: string): Promise<Metamodel[]> {
    return apiService.get<Metamodel[]>(this.basePath, { params: { author } });
  }

  /**
   * Validate a metamodel (change status to validated)
   */
  async validate(id: string): Promise<Metamodel> {
    return apiService.post<Metamodel>(`${this.basePath}/${id}/validate`);
  }

  /**
   * Deprecate a metamodel (change status to deprecated)
   */
  async deprecate(id: string): Promise<Metamodel> {
    return apiService.post<Metamodel>(`${this.basePath}/${id}/deprecate`);
  }

  /**
   * Get edge type constraints for a metamodel
   */
  async getEdgeConstraints(id: string): Promise<EdgeTypeConstraint[]> {
    return apiService.get<EdgeTypeConstraint[]>(`${this.basePath}/${id}/edge-constraints`);
  }

  /**
   * Get complete metamodel graph with all nodes and edges
   */
  async getGraph(id: string): Promise<{
    graph: {
      id: string;
      name: string;
      description?: string;
      type: string;
      node_types: string[];
      edge_types: string[];
      metrics: { nodes: number; edges: number };
      owner_id?: string;
      created_at: string;
      updated_at?: string;
    };
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
  }> {
    return apiService.get(`${this.basePath}/${id}/graph`);
  }
}

export const metamodelService = new MetamodelService();
