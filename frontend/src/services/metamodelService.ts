import { BaseService } from "./base.service";
import { Metamodel, MetamodelCreate, MetamodelUpdate } from "@/types/metamodel";
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
}

export const metamodelService = new MetamodelService();
