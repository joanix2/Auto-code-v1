/**
 * Copilot Assignment Service - API calls for GitHub Copilot assignment
 */
import { apiService } from "./api.service";

export interface AssignToCopilotRequest {
  base_branch?: string;
  custom_instructions?: string;
}

export interface AssignToCopilotResponse {
  success: boolean;
  message: string;
  issue_id: string;
  assigned_to_copilot: boolean;
  github_issue_number?: number;
}

export interface CopilotAvailabilityResponse {
  available: boolean;
  message: string;
  bot_id?: string;
}

class CopilotService {
  private basePath = "/api/copilot";

  /**
   * Check if GitHub Copilot coding agent is available for a repository
   */
  async checkAvailability(repositoryId: string): Promise<CopilotAvailabilityResponse> {
    return apiService.get<CopilotAvailabilityResponse>(`${this.basePath}/availability/${repositoryId}`);
  }

  /**
   * Assign an issue to GitHub Copilot coding agent
   */
  async assignIssue(issueId: string, options?: AssignToCopilotRequest): Promise<AssignToCopilotResponse> {
    return apiService.post<AssignToCopilotResponse>(`${this.basePath}/assign/${issueId}`, options || {});
  }

  /**
   * Unassign an issue from GitHub Copilot coding agent
   */
  async unassignIssue(issueId: string): Promise<AssignToCopilotResponse> {
    return apiService.delete<AssignToCopilotResponse>(`${this.basePath}/assign/${issueId}`);
  }
}

export const copilotService = new CopilotService();
export default copilotService;
