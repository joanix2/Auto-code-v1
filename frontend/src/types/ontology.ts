export interface OntologyGraph {
  id: string;
  name: string;
  description?: string;
  node_count: number;
  edge_count: number;
  created_at: string;
  updated_at?: string;
}

export interface OntologyGraphCreate {
  name: string;
  description?: string;
}

export type OntologyGraphUpdate = Partial<OntologyGraphCreate>;
