/**
 * Repository Types
 */

export interface Repository {
  id: string;
  github_id: number;
  owner_username: string;
  name: string;
  full_name: string;
  description?: string;
  is_private: boolean;
  default_branch: string;
  url?: string; // GitHub URL
  html_url?: string;
  clone_url?: string;
  language?: string;
  stargazers_count?: number;
  forks_count?: number;
  open_issues_count?: number;
  github_created_at?: string;
  github_pushed_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface RepositoryCreate {
  name: string;
  description?: string;
  private?: boolean;
}

export interface RepositoryUpdate {
  description?: string;
  default_branch?: string;
}
