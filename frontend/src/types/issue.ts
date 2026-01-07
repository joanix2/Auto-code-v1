/**
 * Issue Types
 */

export type IssueStatus = "open" | "in_progress" | "review" | "closed";
export type IssuePriority = "low" | "medium" | "high" | "urgent";
export type IssueType = "bug" | "feature" | "documentation" | "refactor";

export interface Issue {
  id: string;
  repository_id: string;
  title: string;
  description: string;
  author_username: string;

  // GitHub integration
  github_issue_number?: number;
  github_issue_url?: string;
  github_branch_name?: string;
  github_pr_number?: number;
  github_pr_url?: string;

  // Metadata
  status: IssueStatus;
  priority: IssuePriority;
  issue_type: IssueType;

  // Copilot
  assigned_to_copilot: boolean;
  copilot_started_at?: string;

  // Timestamps
  created_at: string;
  updated_at?: string;
}

export interface IssueCreate {
  repository_id: string;
  title: string;
  description: string;
  priority?: IssuePriority;
  issue_type?: IssueType;
}

export interface IssueUpdate {
  title?: string;
  description?: string;
  status?: IssueStatus;
  priority?: IssuePriority;
  github_branch_name?: string;
  github_pr_number?: number;
  github_pr_url?: string;
  assigned_to_copilot?: boolean;
}
