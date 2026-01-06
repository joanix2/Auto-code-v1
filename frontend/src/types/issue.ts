/**
 * Issue Types
 */

export type IssueStatus = "open" | "closed";

export interface Issue {
  id: string;
  repository_id: string;
  github_id: number;
  number: number;
  title: string;
  description: string;
  status: IssueStatus;
  html_url: string;
  labels: string[];
  assigned_to_copilot: boolean;
  created_at: string;
  updated_at?: string;
}

export interface IssueCreate {
  repository_id: string;
  github_id: number;
  number: number;
  title: string;
  description?: string;
  status?: IssueStatus;
  html_url?: string;
  labels?: string[];
}

export interface IssueUpdate {
  title?: string;
  description?: string;
  status?: IssueStatus;
  labels?: string[];
  assigned_to_copilot?: boolean;
}
