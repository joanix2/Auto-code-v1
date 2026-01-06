/**
 * Repository Types
 */

export interface Repository {
  id: string;
  github_id: number;
  owner: string;
  name: string;
  full_name: string;
  description?: string;
  is_private: boolean;
  default_branch: string;
  html_url: string;
  clone_url: string;
  created_at: string;
  updated_at?: string;
}

export interface RepositoryCreate {
  github_id: number;
  owner: string;
  name: string;
  full_name: string;
  description?: string;
  is_private?: boolean;
  default_branch?: string;
  html_url?: string;
  clone_url?: string;
}

export interface RepositoryUpdate {
  description?: string;
  default_branch?: string;
}
