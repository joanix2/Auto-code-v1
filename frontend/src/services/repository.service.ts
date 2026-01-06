/**
 * Repository Service - API calls for repositories
 */
import { Repository, RepositoryCreate, RepositoryUpdate } from "../types";
import { apiService } from "./api.service";

class RepositoryService {
  private basePath = "/api/repositories";

  /**
   * Fetch all repositories from GitHub and sync to database
   */
  async syncRepositories(username?: string): Promise<Repository[]> {
    return apiService.post<Repository[]>(`${this.basePath}/sync`, { username });
  }

  /**
   * Get all repositories
   */
  async getAll(): Promise<Repository[]> {
    return apiService.get<Repository[]>(this.basePath);
  }

  /**
   * Get repository by ID
   */
  async getById(id: string): Promise<Repository> {
    return apiService.get<Repository>(`${this.basePath}/${id}`);
  }

  /**
   * Get repository by full name (owner/repo)
   */
  async getByFullName(fullName: string): Promise<Repository> {
    return apiService.get<Repository>(`${this.basePath}/full-name/${fullName}`);
  }

  /**
   * Get repositories by owner
   */
  async getByOwner(owner: string): Promise<Repository[]> {
    return apiService.get<Repository[]>(`${this.basePath}/owner/${owner}`);
  }

  /**
   * Create a new repository
   */
  async create(data: RepositoryCreate): Promise<Repository> {
    return apiService.post<Repository>(this.basePath, data);
  }

  /**
   * Update a repository
   */
  async update(id: string, data: RepositoryUpdate): Promise<Repository> {
    return apiService.patch<Repository>(`${this.basePath}/${id}`, data);
  }

  /**
   * Delete a repository
   */
  async delete(id: string): Promise<void> {
    return apiService.delete<void>(`${this.basePath}/${id}`);
  }

  /**
   * Sync issues for a specific repository
   */
  async syncIssues(id: string): Promise<{ success: boolean; synced_count: number }> {
    return apiService.post(`${this.basePath}/${id}/sync-issues`);
  }
}

export const repositoryService = new RepositoryService();
export default repositoryService;
