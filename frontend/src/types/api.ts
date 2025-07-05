// API response types

export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  repository_url: string;
  provider: 'github' | 'gitlab' | 'bitbucket';
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  project_id: string;
  type: 'claude_code' | 'code_review' | 'issue_analysis' | 'pr_creation' | 'custom';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  prompt: string;
  result?: any;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface CreateTaskRequest {
  prompt: string;
  type: Task['type'];
  project_id?: string;
}

export interface GitProvider {
  id: string;
  name: string;
  enabled: boolean;
}

export interface Repository {
  id: string;
  name: string;
  full_name: string;
  description: string | null;
  private: boolean;
  default_branch: string;
  url: string;
  clone_url: string;
}

export interface Issue {
  id: string;
  number: number;
  title: string;
  body: string;
  state: string;
  author: string;
  labels: string[];
  created_at: string;
  updated_at: string;
}

export interface PullRequest {
  id: string;
  number: number;
  title: string;
  body: string;
  state: string;
  source_branch: string;
  target_branch: string;
  author: string;
  created_at: string;
  updated_at: string;
}

export interface Provider {
  id: string;
  name: string;
  type: string;
  status: string;
  capabilities: string[];
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  repository_url: string;
  provider: Project['provider'];
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}