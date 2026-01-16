export interface Metamodel {
  id: string;
  name: string;
  description?: string;
  version: string;
  node_count: number; // Nombre de concepts/nœuds dans le métamodèle
  edge_count: number; // Nombre de relations/arêtes
  created_at: string;
  updated_at?: string;
  owner_id?: string; // Propriétaire du métamodèle
  status?: "draft" | "validated" | "deprecated";

  // Aliases pour rétro-compatibilité (lecture seule)
  concepts?: number;
  relations?: number;
  author?: string;
}

export interface MetamodelCreate {
  name: string;
  description?: string;
  version: string;
  node_count?: number;
  edge_count?: number;
  status?: "draft" | "validated" | "deprecated";
}

export type MetamodelUpdate = Partial<MetamodelCreate>;
