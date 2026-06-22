/**
 * DSL Service — now maps to the rewriting-logic Language API.
 *
 * Backward-compatible wrapper around /api/languages.
 */

import { apiService } from "./api.service";

export interface DSLGraph {
  id: string;
  name: string;
  description: string;
  version: string;
  node_count: number;
  edge_count: number;
  status: string;
  owner_id?: string;
}

export interface M3NodeData {
  id: string;
  label: string;
  name: string;
  description?: string;
  type?: string;
  x?: number;
  y?: number;
  [key: string]: unknown;
}

export interface M3EdgeData {
  id: string;
  type: string;
  source: string;
  target: string;
  label?: string;
  [key: string]: unknown;
}

export interface DSLGraphResponse {
  dsl: DSLGraph;
  nodes: M3NodeData[];
  edges: M3EdgeData[];
  edgeConstraints: unknown[];
}

class DSLService {
  protected basePath = "/api/languages";

  async getAll(params?: Record<string, unknown>): Promise<DSLGraph[]> {
    const langs = await apiService.get<any[]>(this.basePath, { params });
    return langs.map((l: any) => ({
      id: l.id,
      name: l.name,
      description: l.description || "",
      version: "1.0",
      node_count: l.node_count || 0,
      edge_count: l.edge_count || 0,
      status: "active",
    }));
  }

  async getById(id: string): Promise<DSLGraph> {
    const lang = await apiService.get<any>(`${this.basePath}/${id}`);
    return {
      id: lang.id,
      name: lang.name,
      description: lang.description || "",
      version: "1.0",
      node_count: lang.node_count || 0,
      edge_count: lang.edge_count || 0,
      status: "active",
    };
  }

  async create(data: { name: string; description?: string; version?: string }): Promise<DSLGraph> {
    const lang = await apiService.post<any>(this.basePath, {
      name: data.name,
      description: data.description || "",
    });
    return {
      id: lang.id,
      name: lang.name,
      description: lang.description || "",
      version: "1.0",
      node_count: 0,
      edge_count: 0,
      status: "active",
    };
  }

  async update(id: string, data: Record<string, unknown>): Promise<DSLGraph> {
    return this.getById(id);
  }

  async delete(id: string): Promise<void> {
    await apiService.delete(`${this.basePath}/${id}`);
  }

  async getGraph(id: string): Promise<DSLGraphResponse> {
    const resp = await apiService.get<any>(`${this.basePath}/${id}/graph`);
    const lang = resp.language || resp;
    return {
      dsl: {
        id: lang.id,
        name: lang.name,
        description: lang.description || "",
        version: "1.0",
        node_count: lang.node_count || 0,
        edge_count: lang.edge_count || 0,
        status: "active",
      },
      nodes: (resp.nodes || []).map((n: any) => ({
        id: n.id,
        name: n.name,
        description: n.description || "",
        type: n.label,
        label: n.name,
        ...n,
      })),
      edges: resp.edges || [],
      edgeConstraints: [],
    };
  }
}

export const dslService = new DSLService();
