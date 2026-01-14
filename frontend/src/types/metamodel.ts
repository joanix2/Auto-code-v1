export interface Metamodel {
  id: string;
  name: string;
  description?: string;
  version: string;
  concepts: number; // Nombre de concepts dans le métamodèle
  relations: number; // Nombre de relations
  created_at: string;
  updated_at?: string;
  author?: string;
  status?: "draft" | "validated" | "deprecated";
}

export interface MetamodelCreate {
  name: string;
  description?: string;
  version: string;
  concepts: number;
  relations: number;
  author?: string;
  status?: "draft" | "validated" | "deprecated";
}

export type MetamodelUpdate = Partial<MetamodelCreate>;
