/**
 * Edge Service - API calls for MDE edges
 */
import { apiService } from "./api.service";

export interface Edge {
  id: string;
  source: string;
  target: string;
  type: string;
  label?: string;
}

export interface EdgeCreate {
  graph_id: string;
  source_id: string;
  target_id: string;
  edge_type: string;
}

class EdgeService {
  private basePath = "/api/edges";

  /**
   * Create a new edge between two nodes
   */
  async create(edgeData: EdgeCreate): Promise<Edge> {
    return apiService.post<Edge>(this.basePath, edgeData);
  }

  /**
   * Delete an edge between two nodes
   */
  async delete(sourceId: string, targetId: string, edgeType: string): Promise<{ message: string }> {
    return apiService.delete<{ message: string }>(`${this.basePath}/${sourceId}/${targetId}/${edgeType}`);
  }
}

export const edgeService = new EdgeService();
