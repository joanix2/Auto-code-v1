/**
 * Base Service — abstract CRUD service with typed methods.
 */

import { apiService } from "./api.service";

export interface SyncResponse<T> {
  synced: T[];
  errors: Array<{ item: string; error: string }>;
}

export class BaseService<T, CreateDTO = Partial<T>, UpdateDTO = Partial<T>> {
  protected basePath = "";

  async getAll(params?: Record<string, unknown>): Promise<T[]> {
    return apiService.get<T[]>(this.basePath, { params });
  }

  async getById(id: string): Promise<T> {
    return apiService.get<T>(`${this.basePath}/${id}`);
  }

  async create(data: CreateDTO): Promise<T> {
    return apiService.post<T>(this.basePath, data);
  }

  async update(id: string, data: UpdateDTO): Promise<T> {
    return apiService.put<T>(`${this.basePath}/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    return apiService.delete(`${this.basePath}/${id}`);
  }
}

export class SyncableService<T, CreateDTO = Partial<T>, UpdateDTO = Partial<T>> extends BaseService<
  T,
  CreateDTO,
  UpdateDTO
> {
  async sync(data: CreateDTO[]): Promise<SyncResponse<T>> {
    return apiService.post<SyncResponse<T>>(`${this.basePath}/sync`, data);
  }
}
