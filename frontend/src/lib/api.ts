import type {
  User,
  AuthResponse,
  Project,
  Task,
  CreateTaskRequest,
  GitProvider,
  Repository,
  Issue,
  PullRequest,
  Provider,
  CreateProjectRequest,
  RegisterRequest,
  LoginRequest
} from '@/types/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api';

interface RequestOptions extends RequestInit {
  token?: string;
}

class ApiClient {
  private baseUrl: string;
  private token?: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { token, ...fetchOptions } = options;
    const authToken = token || this.token;

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { Authorization: `Bearer ${authToken}` }),
        ...fetchOptions.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: 'An error occurred',
      }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password } as LoginRequest),
    });
  }

  async register(email: string, password: string, name: string) {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name } as RegisterRequest),
    });
  }

  // Project endpoints
  async getProjects() {
    return this.request<Project[]>('/projects');
  }

  async getProject(id: string) {
    return this.request<Project>(`/projects/${id}`);
  }

  async createProject(data: CreateProjectRequest) {
    return this.request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Task endpoints
  async getTasks(projectId?: string) {
    const query = projectId ? `?project_id=${projectId}` : '';
    return this.request<Task[]>(`/tasks${query}`);
  }

  async getTask(id: string) {
    return this.request<Task>(`/tasks/${id}`);
  }

  async createTask(data: CreateTaskRequest) {
    return this.request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Git provider endpoints
  async getGitProviders() {
    return this.request<GitProvider[]>('/git-providers');
  }

  async getRepositories(provider: string) {
    return this.request<Repository[]>(`/git-providers/${provider}/repositories`);
  }

  async getRepository(provider: string, owner: string, repo: string) {
    return this.request<Repository>(
      `/git-providers/${provider}/repositories/${owner}/${repo}`
    );
  }

  async getIssues(provider: string, owner: string, repo: string, state = 'open') {
    return this.request<Issue[]>(
      `/git-providers/${provider}/repositories/${owner}/${repo}/issues?state=${state}`
    );
  }

  async getIssue(provider: string, owner: string, repo: string, issueNumber: number) {
    return this.request<Issue>(
      `/git-providers/${provider}/repositories/${owner}/${repo}/issues/${issueNumber}`
    );
  }

  async getPullRequests(provider: string, owner: string, repo: string, state = 'open') {
    return this.request<PullRequest[]>(
      `/git-providers/${provider}/repositories/${owner}/${repo}/pulls?state=${state}`
    );
  }

  async getPullRequest(provider: string, owner: string, repo: string, prNumber: number) {
    return this.request<PullRequest>(
      `/git-providers/${provider}/repositories/${owner}/${repo}/pulls/${prNumber}`
    );
  }

  // AI provider endpoints
  async getProviders() {
    return this.request<Provider[]>('/providers');
  }
}

export const api = new ApiClient();
export default api;