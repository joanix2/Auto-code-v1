/**
 * Language Service — API client for rewriting-logic languages.
 *
 * Each language contains sorts, ops, equations, rules, etc.
 */

import { apiService } from "./api.service";

export interface Language {
  id: string;
  name: string;
  description: string;
  node_count: number;
  edge_count: number;
}

export interface M3NodeData {
  id: string;
  label: string;
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

export interface LanguageGraph {
  language: Language;
  nodes: M3NodeData[];
  edges: M3EdgeData[];
}

class LanguageService {
  async list(): Promise<Language[]> {
    return apiService.get<Language[]>("/api/languages");
  }

  async create(data: { name: string; description?: string }): Promise<Language> {
    return apiService.post<Language>("/api/languages", data);
  }

  async get(id: string): Promise<Language> {
    return apiService.get<Language>(`/api/languages/${id}`);
  }

  async delete(id: string): Promise<void> {
    return apiService.delete(`/api/languages/${id}`);
  }

  async getGraph(id: string): Promise<LanguageGraph> {
    return apiService.get<LanguageGraph>(`/api/languages/${id}/graph`);
  }

  async createSort(langId: string, data: { name: string; description?: string; [key: string]: unknown }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>(`/api/languages/${langId}/sorts`, data);
  }

  async createOp(langId: string, data: { name: string; result_sort: string; params?: string[]; description?: string }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>(`/api/languages/${langId}/ops`, data);
  }

  async createEquation(langId: string, data: { name: string; lhs?: string; rhs?: string }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>(`/api/languages/${langId}/equations`, data);
  }

  async createRule(langId: string, data: { name: string; lhs?: string; rhs?: string }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>(`/api/languages/${langId}/rules`, data);
  }

  async createInvariant(langId: string, data: { name: string; condition?: string }): Promise<M3NodeData> {
    return apiService.post<M3NodeData>(`/api/languages/${langId}/invariants`, data);
  }
}

export const languageService = new LanguageService();
