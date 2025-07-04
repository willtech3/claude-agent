export interface Task {
  id: string;
  projectId: string;
  type: TaskType;
  status: TaskStatus;
  payload: TaskPayload;
  result?: TaskResult;
  createdAt: Date;
  updatedAt: Date;
  startedAt?: Date;
  completedAt?: Date;
}

export enum TaskType {
  CODE_REVIEW = 'CODE_REVIEW',
  ISSUE_ANALYSIS = 'ISSUE_ANALYSIS',
  PR_CREATION = 'PR_CREATION',
  CODE_GENERATION = 'CODE_GENERATION',
  DOCUMENTATION = 'DOCUMENTATION',
}

export enum TaskStatus {
  PENDING = 'PENDING',
  QUEUED = 'QUEUED',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

export interface TaskPayload {
  [key: string]: any;
}

export interface TaskResult {
  success: boolean;
  data?: any;
  error?: string;
  artifacts?: string[];
}