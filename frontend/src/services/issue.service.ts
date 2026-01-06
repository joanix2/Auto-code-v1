/**
 * Issue Service - API calls for issues
 */
import { Issue, IssueCreate, IssueUpdate } from "../types";
import { apiService } from "./api.service";

class IssueService {
  private basePath = "/api/issues";

  /**
   * Get all issues (optionally filter by repository and status)
   */
  async getAll(repositoryId?: string, status?: string): Promise<Issue[]> {
    const params: Record<string, string> = {};
    if (repositoryId) params.repository_id = repositoryId;
    if (status) params.status = status;

    return apiService.get<Issue[]>(this.basePath, { params });
  }

  /**
   * Get issue by ID
   */
  async getById(id: string): Promise<Issue> {
    return apiService.get<Issue>(`${this.basePath}/${id}`);
  }

  /**
   * Get issues by repository
   */
  async getByRepository(repositoryId: string, status?: string): Promise<Issue[]> {
    return this.getAll(repositoryId, status);
  }

  /**
   * Create a new issue
   */
  async create(data: IssueCreate): Promise<Issue> {
    return apiService.post<Issue>(this.basePath, data);
  }

  /**
   * Update an issue
   */
  async update(id: string, data: IssueUpdate): Promise<Issue> {
    return apiService.patch<Issue>(`${this.basePath}/${id}`, data);
  }

  /**
   * Delete an issue
   */
  async delete(id: string): Promise<void> {
    return apiService.delete<void>(`${this.basePath}/${id}`);
  }

  /**
   * Assign issue to Copilot
   */
  async assignToCopilot(
    id: string,
    options?: {
      base_branch?: string;
      custom_instructions?: string;
    }
  ): Promise<{ success: boolean; message: string }> {
    return apiService.post(`${this.basePath}/${id}/assign-to-copilot`, options);
  }

  /**
   * Get issues assigned to Copilot
   */
  async getCopilotIssues(repositoryId?: string): Promise<Issue[]> {
    const issues = await this.getAll(repositoryId);
    return issues.filter((issue) => issue.assigned_to_copilot);
  }
}

export const issueService = new IssueService();
export default issueService;
