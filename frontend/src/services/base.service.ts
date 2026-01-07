/**
 * Base Service - Abstract class for all entity services
 * Provides common CRUD operations and optional sync functionality
 */
import { apiService } from "./api.service";

export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at?: string; // Optional because some entities may not have it
}

export interface SyncResponse<T> {
  success: boolean;
  synced_count: number;
  data?: T[];
}

/**
 * Abstract base service providing CRUD operations
 */
export abstract class BaseService<TEntity extends BaseEntity, TCreate = Partial<TEntity>, TUpdate = Partial<TEntity>> {
  protected abstract basePath: string;

  /**
   * Get all entities (optionally with filters)
   */
  async getAll(params?: Record<string, string>): Promise<TEntity[]> {
    return apiService.get<TEntity[]>(this.basePath, { params });
  }

  /**
   * Get entity by ID
   */
  async getById(id: string): Promise<TEntity> {
    return apiService.get<TEntity>(`${this.basePath}/${id}`);
  }

  /**
   * Create a new entity
   */
  async create(data: TCreate): Promise<TEntity> {
    return apiService.post<TEntity>(this.basePath, data);
  }

  /**
   * Update an entity
   */
  async update(id: string, data: TUpdate): Promise<TEntity> {
    return apiService.patch<TEntity>(`${this.basePath}/${id}`, data);
  }

  /**
   * Delete an entity
   */
  async delete(id: string): Promise<void> {
    return apiService.delete<void>(`${this.basePath}/${id}`);
  }
}

/**
 * Abstract service with GitHub synchronization support
 */
export abstract class SyncableService<TEntity extends BaseEntity, TCreate = Partial<TEntity>, TUpdate = Partial<TEntity>> extends BaseService<TEntity, TCreate, TUpdate> {
  /**
   * Sync entities from GitHub to local database
   * Override this method to implement specific sync logic
   */
  abstract sync(params?: Record<string, unknown>): Promise<SyncResponse<TEntity>>;
}
