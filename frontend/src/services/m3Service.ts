/**
 * M3 Service - Fetches meta-metamodel configuration from backend
 *
 * This service provides access to the M3 (meta-metamodel) configuration,
 * which defines the types of nodes and edges available in the system.
 */
import axios from "axios";
import { M3NodeType, M3EdgeType } from "@/types/m3";

// Re-export for convenience
export type { M3NodeType, M3EdgeType } from "@/types/m3";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface GenderType {
  value: "m" | "f" | "n";
}

export interface M3Config {
  nodeTypes: M3NodeType[];
  edgeTypes: M3EdgeType[];
}

class M3Service {
  private baseUrl: string;
  private cachedConfig: M3Config | null = null;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/m3`;
  }

  /**
   * Get complete M3 configuration (cached)
   */
  async getConfig(): Promise<M3Config> {
    if (this.cachedConfig) {
      return this.cachedConfig;
    }

    const response = await axios.get<M3Config>(`${this.baseUrl}/config`);
    this.cachedConfig = response.data;
    return this.cachedConfig;
  }

  /**
   * Get all node types
   */
  async getNodeTypes(): Promise<M3NodeType[]> {
    const response = await axios.get<M3NodeType[]>(`${this.baseUrl}/node-types`);
    return response.data;
  }

  /**
   * Get a specific node type by ID
   */
  async getNodeType(typeId: string): Promise<M3NodeType> {
    const response = await axios.get<M3NodeType>(`${this.baseUrl}/node-types/${typeId}`);
    return response.data;
  }

  /**
   * Get all edge types
   */
  async getEdgeTypes(): Promise<M3EdgeType[]> {
    const response = await axios.get<M3EdgeType[]>(`${this.baseUrl}/edge-types`);
    return response.data;
  }

  /**
   * Get a specific edge type by ID
   */
  async getEdgeType(typeId: string): Promise<M3EdgeType> {
    const response = await axios.get<M3EdgeType>(`${this.baseUrl}/edge-types/${typeId}`);
    return response.data;
  }

  /**
   * Clear cached configuration (call this if M3 config changes)
   */
  clearCache(): void {
    this.cachedConfig = null;
  }

  /**
   * Get article with capital letter
   */
  getArticleMaj(article: string): string {
    return article.charAt(0).toUpperCase() + article.slice(1);
  }
}

export const m3Service = new M3Service();
