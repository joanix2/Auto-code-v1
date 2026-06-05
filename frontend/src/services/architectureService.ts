import { BaseService } from "./base.service";
import { apiService } from "./api.service";

export interface ArchitectureGraph {
  id: string;
  name: string;
  description?: string;
  parent_dsl_id?: string;
  node_count: number;
  edge_count: number;
  created_at: string;
  updated_at?: string;
}

export interface ArchitectureGraphCreate {
  name: string;
  description?: string;
  parent_dsl_id?: string;
}

export type ArchitectureGraphUpdate = Partial<ArchitectureGraphCreate>;

class ArchitectureService extends BaseService<ArchitectureGraph, ArchitectureGraphCreate, ArchitectureGraphUpdate> {
  protected basePath = "/api/architecture";
}

export const architectureService = new ArchitectureService();
export default architectureService;
