export interface ProviderConfig {
  type: 'github' | 'gitlab' | 'bitbucket';
  baseUrl?: string;
  apiToken: string;
}

export interface Repository {
  id: string;
  name: string;
  fullName: string;
  description?: string;
  private: boolean;
  defaultBranch: string;
  url: string;
  cloneUrl: string;
}

export interface Issue {
  id: string;
  number: number;
  title: string;
  body: string;
  state: 'open' | 'closed';
  author: string;
  labels: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface PullRequest {
  id: string;
  number: number;
  title: string;
  body: string;
  state: 'open' | 'closed' | 'merged';
  sourceBranch: string;
  targetBranch: string;
  author: string;
  createdAt: Date;
  updatedAt: Date;
}