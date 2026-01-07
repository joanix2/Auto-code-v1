/**
 * Issue Service - API calls for issues
 */
import { Issue, IssueCreate, IssueUpdate } from "../types";
import { SyncableService, SyncResponse } from "./base.service";
import { apiService } from "./api.service";
import { copilotService, AssignToCopilotResponse } from "./copilot.service";

class IssueService extends SyncableService<Issue, IssueCreate, IssueUpdate> {
  protected basePath = "/api/issues";

  /**
   * Sync issues from GitHub for a specific repository
   */
  async sync(params?: { repositoryId: string }): Promise<SyncResponse<Issue>> {
    if (!params?.repositoryId) {
      throw new Error("Repository ID is required for syncing issues");
    }

    const response = await apiService.post<SyncResponse<Issue>>(`/api/repositories/${params.repositoryId}/sync-issues`);
    return response;
  }

  /**
   * Get all issues (optionally filter by repository and status)
   * Override to provide custom filtering
   */
  async getAllIssues(repositoryId?: string, status?: string): Promise<Issue[]> {
    const params: Record<string, string> = {};
    if (repositoryId) params.repository_id = repositoryId;
    if (status) params.status = status;

    return super.getAll(params);
  }

  /**
   * Get issues by repository
   */
  async getByRepository(repositoryId: string, status?: string): Promise<Issue[]> {
    return this.getAllIssues(repositoryId, status);
  }

  /**
   * Assign issue to Copilot
   * Uses the dedicated Copilot assignment service
   */
  async assignToCopilot(
    id: string,
    options?: {
      base_branch?: string;
      custom_instructions?: string;
    }
  ): Promise<AssignToCopilotResponse> {
    return copilotService.assignIssue(id, options);
  }

  /**
   * Unassign issue from Copilot
   */
  async unassignFromCopilot(id: string): Promise<AssignToCopilotResponse> {
    return copilotService.unassignIssue(id);
  }

  /**
   * Get issues assigned to Copilot
   */
  async getCopilotIssues(repositoryId?: string): Promise<Issue[]> {
    const issues = await this.getAllIssues(repositoryId);
    return issues.filter((issue) => issue.assigned_to_copilot);
  }
}

export const issueService = new IssueService();
export default issueService;
