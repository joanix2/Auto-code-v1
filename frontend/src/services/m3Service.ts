/**
 * M3 Service — API client for the rewriting-logic M3 graph.
 *
 * The M3 is a graph of 7 Neo4j node types:
 *   :Sort, :Op, :Equation, :Rule, :ConditionalRule, :Strategy, :Invariant
 */

import { apiService } from "./api.service";

export interface M3NodeData {
  id: string;
  label: string; // "Sort" | "Op" | "Equation" | "Rule" | "ConditionalRule" | "Strategy" | "Invariant"
  name: string;
  description?: string;
  [key: string]: unknown;
}

export interface M3EdgeData {
  id: string;
  type: string;
  source: string;
  target: string;
  [key: string]: unknown;
}

export interface M3GraphData {
  nodes: M3NodeData[];
  edges: M3EdgeData[];
}

class M3Service {
  async getGraph(): Promise<M3GraphData> {
    return apiService.get<M3GraphData>("/api/m3/graph");
  }

  async listSorts(): Promise<M3NodeData[]> {
    return apiService.get<M3NodeData[]>("/api/m3/sorts");
  }

  async createSort(data: { name: string; description?: string; [key: string]: unknown }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>("/api/m3/sorts", data);
  }

  async listOps(): Promise<M3NodeData[]> {
    return apiService.get<M3NodeData[]>("/api/m3/ops");
  }

  async createOp(data: { name: string; result_sort: string; params?: string[]; description?: string }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>("/api/m3/ops", data);
  }

  async listEquations(): Promise<M3NodeData[]> {
    return apiService.get<M3NodeData[]>("/api/m3/equations");
  }

  async createEquation(data: { name: string; lhs?: string; rhs?: string; description?: string }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>("/api/m3/equations", data);
  }

  async listRules(): Promise<M3NodeData[]> {
    return apiService.get<M3NodeData[]>("/api/m3/rules");
  }

  async createRule(data: { name: string; lhs?: string; rhs?: string; description?: string }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>("/api/m3/rules", data);
  }

  async listConditionalRules(): Promise<M3NodeData[]> {
    return apiService.get<M3NodeData[]>("/api/m3/conditional-rules");
  }

  async listStrategies(): Promise<M3NodeData[]> {
    return apiService.get<M3NodeData[]>("/api/m3/strategies");
  }

  async listInvariants(): Promise<M3NodeData[]> {
    return apiService.get<M3NodeData[]>("/api/m3/invariants");
  }

  async createInvariant(data: { name: string; condition?: string; description?: string }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>("/api/m3/invariants", data);
  }
}

export const m3Service = new M3Service();
