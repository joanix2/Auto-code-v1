/**
 * Repository Service - API calls for repositories
 */
import { Repository, RepositoryCreate, RepositoryUpdate } from "../types";
import { SyncableService, SyncResponse } from "./base.service";
import { apiService } from "./api.service";

class RepositoryService extends SyncableService<Repository, RepositoryCreate, RepositoryUpdate> {
  protected basePath = "/api/repositories";

  /**
   * Sync repositories from GitHub to database
   */
  async sync(params?: { username?: string }): Promise<SyncResponse<Repository>> {
    const response = await apiService.post<{ count: number; repositories: Repository[] }>(`${this.basePath}/sync`, { username: params?.username });
    return {
      success: true,
      synced_count: response.count,
      data: response.repositories,
    };
  }

  /**
   * Fetch all repositories from GitHub and sync to database
   * @deprecated Use sync() instead
   */
  async syncRepositories(username?: string): Promise<Repository[]> {
    const response = await this.sync({ username });
    return response.data || [];
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
   * Sync issues for a specific repository
   * @deprecated This should be done through IssueService.sync()
   */
  async syncIssues(id: string): Promise<{ success: boolean; synced_count: number }> {
    return apiService.post(`${this.basePath}/${id}/sync-issues`);
  }
}

export const repositoryService = new RepositoryService();
export default repositoryService;
