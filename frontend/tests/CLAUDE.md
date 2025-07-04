# CLAUDE.md - Frontend Testing Guidelines

## Inheritance
- **Extends:** /CLAUDE.md (root)
- **Overrides:** None (CRITICAL RULES cannot be overridden)
- **Scope:** All JavaScript/TypeScript test files in frontend/tests, frontend/src/**/*.test.{js,jsx,ts,tsx}

## Rules

**Context:** This document provides testing best practices and guidelines for Claude Agent frontend. Read this when writing tests for React components, hooks, utilities, or reviewing test quality.

---

# Frontend Testing Guidelines for Claude Agent

This document outlines testing best practices for our Next.js React frontend with a focus on Jules-inspired UI components and real-time features.

## Table of Contents
- [Testing Philosophy](#testing-philosophy)
- [Test Quality Standards](#test-quality-standards)
- [Mock Usage Guidelines](#mock-usage-guidelines)
- [Coverage Requirements](#coverage-requirements)
- [Test Organization](#test-organization)
- [Testing React Components](#testing-react-components)
- [Testing Async Operations](#testing-async-operations)
- [Testing WebSocket Connections](#testing-websocket-connections)
- [Common Anti-Patterns](#common-anti-patterns)
- [Best Practices by Feature](#best-practices-by-feature)

## Testing Philosophy

### Core Principles
1. **Test user behavior, not implementation** - Test what users see and do
2. **Avoid testing internals** - Don't test state, test outcomes
3. **Prefer Testing Library queries** - Use accessible queries that mirror user behavior
4. **Write tests that inspire refactoring confidence** - Tests shouldn't break when improving code

### Testing Pyramid for Frontend
```
         /\
        /  \    E2E Tests (Critical user journeys)
       /    \
      /------\  Integration Tests (Features with API)
     /        \
    /----------\ Unit Tests (Components, hooks, utils)
```

## Test Quality Standards

### High-Quality Test Characteristics
- **User-focused**: Tests interact with components like users would
- **Resilient**: Survive refactoring that doesn't change behavior
- **Descriptive**: Test names explain the user scenario
- **Fast**: Component tests < 200ms
- **Maintainable**: Easy to understand and modify

### Example of a Good Test
```javascript
import { render, screen, userEvent } from '@testing-library/react';
import { TaskSubmissionForm } from '@/features/tasks/TaskSubmissionForm';

describe('TaskSubmissionForm', () => {
  it('allows user to submit a coding task', async () => {
    // Arrange
    const user = userEvent.setup();
    const onSubmit = jest.fn();
    render(<TaskSubmissionForm onSubmit={onSubmit} />);
    
    // Act - interact like a user would
    const input = screen.getByPlaceholderText(/describe your task/i);
    await user.type(input, 'Create a React component');
    await user.click(screen.getByRole('button', { name: /submit task/i }));
    
    // Assert outcome, not implementation
    expect(onSubmit).toHaveBeenCalledWith({
      prompt: 'Create a React component'
    });
  });
});
```

## Mock Usage Guidelines

### When to Mock
| What to Mock | Reason |
|--------------|--------|
| API calls (fetch/axios) | Avoid network dependencies |
| WebSocket connections | Control message flow in tests |
| Browser APIs (localStorage, etc) | Ensure consistent behavior |
| External libraries (code editors) | Focus on your code |
| Time-based operations | Control timing |

### When NOT to Mock
| What NOT to Mock | Reason |
|------------------|--------|
| React components | Test real integration |
| React hooks | Test actual behavior |
| Utility functions | Verify real logic |
| CSS modules | Ensure styles apply |

### Prefer MSW for API Mocking
```javascript
// ✅ GOOD - Mock at network level with MSW
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.post('/api/tasks', (req, res, ctx) => {
    return res(ctx.json({ task_id: 'test-123' }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// ❌ AVOID - Mocking fetch directly
global.fetch = jest.fn(() => Promise.resolve({
  json: () => Promise.resolve({ task_id: 'test-123' })
}));
```

## Coverage Requirements

### By Feature Area (Target Goals)
| Area | Target Coverage | Rationale |
|------|-----------------|-----------|
| Components | 80% | User-facing elements need confidence |
| Hooks | 90% | Reusable logic must be reliable |
| Utils | 95% | Pure functions should be thoroughly tested |
| API Client | 85% | Critical for app functionality |
| Overall | 80% | Balanced coverage goal |

**Note**: Prioritize testing critical user paths over achieving high coverage numbers.

## Test Organization

### Directory Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── Button.module.css
│   ├── features/
│   │   ├── tasks/
│   │   │   ├── TaskList.tsx
│   │   │   ├── TaskList.test.tsx
│   │   │   └── __tests__/
│   │   │       └── TaskFlow.integration.test.tsx
│   └── lib/
│       ├── api.ts
│       ├── api.test.ts
│       └── __mocks__/
│           └── api.ts
├── tests/
│   ├── setup.ts          # Jest setup
│   ├── utils.tsx         # Test utilities
│   └── fixtures/         # Shared test data
└── jest.config.js
```

### Naming Conventions
- Component tests: `ComponentName.test.tsx`
- Integration tests: `Feature.integration.test.tsx`
- Test utilities: `tests/utils.tsx`
- Fixtures: `tests/fixtures/[domain].ts`

## Testing React Components

### Use Testing Library Best Practices
```javascript
// ✅ GOOD - Query by accessible roles and text
const submitButton = screen.getByRole('button', { name: /submit/i });
const heading = screen.getByRole('heading', { name: /task details/i });
const input = screen.getByLabelText(/task description/i);

// ❌ BAD - Query by implementation details
const submitButton = screen.getByTestId('submit-btn');
const heading = screen.getByClassName('task-heading');
const input = container.querySelector('#task-input');
```

### Test User Interactions
```javascript
it('shows real-time status updates during task execution', async () => {
  const user = userEvent.setup();
  render(<TaskExecutor />);
  
  // User submits task
  await user.type(screen.getByLabelText(/task/i), 'Build a CLI tool');
  await user.click(screen.getByRole('button', { name: /execute/i }));
  
  // Verify status progression
  expect(screen.getByText(/queued/i)).toBeInTheDocument();
  
  // Simulate WebSocket updates
  await waitFor(() => {
    expect(screen.getByText(/processing/i)).toBeInTheDocument();
  });
  
  // Verify completion
  await waitFor(() => {
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });
});
```

### Test Accessibility
```javascript
it('maintains keyboard navigation for task list', async () => {
  const user = userEvent.setup();
  render(<TaskList tasks={mockTasks} />);
  
  // Tab through items
  await user.tab();
  expect(screen.getByText('Task 1')).toHaveFocus();
  
  await user.tab();
  expect(screen.getByText('Task 2')).toHaveFocus();
  
  // Activate with keyboard
  await user.keyboard('{Enter}');
  expect(screen.getByRole('dialog')).toBeInTheDocument();
});
```

## Testing Async Operations

### API Calls with React Query
```javascript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });
  
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

it('fetches project data on mount', async () => {
  const { result } = renderHook(
    () => useProject('test-project'),
    { wrapper: createWrapper() }
  );
  
  // Initially loading
  expect(result.current.isLoading).toBe(true);
  
  // Wait for success
  await waitFor(() => {
    expect(result.current.isSuccess).toBe(true);
  });
  
  expect(result.current.data).toEqual({
    id: 'test-project',
    name: 'Test Project'
  });
});
```

## Testing WebSocket Connections

### Mock WebSocket for Predictable Tests
```javascript
// tests/mocks/websocket.ts
export class MockWebSocket {
  url: string;
  readyState: number = WebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 0);
  }

  send(data: string) {
    // Mock implementation
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }

  // Helper to simulate incoming messages
  simulateMessage(data: any) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }
}

// In your test
beforeEach(() => {
  global.WebSocket = MockWebSocket as any;
});
```

### Test Real-Time Features
```javascript
it('displays streaming output from agent', async () => {
  render(<AgentOutput taskId="test-123" />);
  
  // Get the WebSocket instance
  const ws = MockWebSocket.instances[0];
  
  // Simulate streaming messages
  act(() => {
    ws.simulateMessage({ type: 'output', content: 'Analyzing codebase...' });
  });
  
  expect(screen.getByText(/analyzing codebase/i)).toBeInTheDocument();
  
  act(() => {
    ws.simulateMessage({ type: 'output', content: 'Creating components...' });
  });
  
  expect(screen.getByText(/creating components/i)).toBeInTheDocument();
  
  // Simulate completion
  act(() => {
    ws.simulateMessage({ type: 'complete', status: 'success' });
  });
  
  expect(screen.getByText(/task completed/i)).toBeInTheDocument();
});
```

## Common Anti-Patterns

### 1. Testing Implementation Details
```javascript
// ❌ BAD - Tests internal state
it('updates state when button clicked', () => {
  const { result } = renderHook(() => useState(0));
  act(() => result.current[1](1));
  expect(result.current[0]).toBe(1);
});

// ✅ GOOD - Tests visible behavior
it('increments counter when button clicked', async () => {
  const user = userEvent.setup();
  render(<Counter />);
  
  await user.click(screen.getByRole('button', { name: /increment/i }));
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```

### 2. Overusing data-testid
```javascript
// ❌ BAD - Relies on test IDs
<button data-testid="submit-task-button">Submit</button>
screen.getByTestId('submit-task-button');

// ✅ GOOD - Uses accessible queries
<button>Submit Task</button>
screen.getByRole('button', { name: /submit task/i });
```

### 3. Testing Third-Party Components
```javascript
// ❌ BAD - Tests library behavior
it('renders Material-UI button with correct variant', () => {
  render(<Button variant="contained" />);
  expect(screen.getByRole('button')).toHaveClass('MuiButton-contained');
});

// ✅ GOOD - Tests your usage
it('submits form when clicking submit button', async () => {
  const onSubmit = jest.fn();
  render(<MyForm onSubmit={onSubmit} />);
  
  await user.click(screen.getByRole('button', { name: /submit/i }));
  expect(onSubmit).toHaveBeenCalled();
});
```

## Best Practices by Feature

### Task Submission Flow
```javascript
describe('Task Submission', () => {
  it('provides feedback during task submission', async () => {
    const user = userEvent.setup();
    render(<TaskSubmissionFlow />);
    
    // Fill form
    await user.type(
      screen.getByLabelText(/describe your task/i),
      'Create a REST API'
    );
    
    // Submit
    await user.click(screen.getByRole('button', { name: /submit/i }));
    
    // Shows loading state
    expect(screen.getByText(/submitting/i)).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
    
    // Shows success
    await waitFor(() => {
      expect(screen.getByText(/task queued successfully/i)).toBeInTheDocument();
    });
    
    // Can view task
    expect(screen.getByRole('link', { name: /view task/i })).toHaveAttribute(
      'href',
      expect.stringContaining('/tasks/')
    );
  });
});
```

### Agent Interaction Interface
```javascript
describe('Agent Interaction', () => {
  it('shows agent actions in timeline view', async () => {
    render(<AgentTimeline taskId="test-123" />);
    
    // Shows initial status
    expect(screen.getByText(/waiting for agent/i)).toBeInTheDocument();
    
    // Simulate agent actions via WebSocket
    const ws = MockWebSocket.instances[0];
    
    act(() => {
      ws.simulateMessage({
        type: 'action',
        action: 'analyzing_repository',
        timestamp: '2024-01-01T10:00:00Z'
      });
    });
    
    const timelineItem = screen.getByRole('listitem');
    expect(timelineItem).toHaveTextContent(/analyzing repository/i);
    expect(timelineItem).toHaveTextContent(/10:00/);
  });
});
```

### File Tree with Changes
```javascript
describe('File Tree', () => {
  it('highlights files modified by agent', () => {
    const files = [
      { path: 'src/App.tsx', status: 'modified' },
      { path: 'src/utils.ts', status: 'created' },
      { path: 'README.md', status: 'unchanged' }
    ];
    
    render(<FileTree files={files} />);
    
    const appFile = screen.getByText('App.tsx').closest('li');
    const utilsFile = screen.getByText('utils.ts').closest('li');
    const readmeFile = screen.getByText('README.md').closest('li');
    
    expect(appFile).toHaveAttribute('data-status', 'modified');
    expect(utilsFile).toHaveAttribute('data-status', 'created');
    expect(readmeFile).not.toHaveAttribute('data-status');
  });
});
```

## Performance Testing

### Measure Render Performance
```javascript
import { measureRender } from '@/tests/utils';

it('renders large task list efficiently', async () => {
  const tasks = Array.from({ length: 1000 }, (_, i) => ({
    id: `task-${i}`,
    title: `Task ${i}`,
    status: 'completed'
  }));
  
  const renderTime = await measureRender(
    <TaskList tasks={tasks} />
  );
  
  // Should render under 100ms even with 1000 items
  expect(renderTime).toBeLessThan(100);
});
```

## Testing Custom Hooks

```javascript
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

describe('useWebSocket', () => {
  it('reconnects on connection loss', async () => {
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws/test')
    );
    
    // Initially connecting
    expect(result.current.status).toBe('connecting');
    
    // Simulate connection
    await waitFor(() => {
      expect(result.current.status).toBe('connected');
    });
    
    // Simulate disconnection
    act(() => {
      MockWebSocket.instances[0].close();
    });
    
    expect(result.current.status).toBe('reconnecting');
    
    // Should attempt reconnection
    await waitFor(() => {
      expect(MockWebSocket.instances).toHaveLength(2);
    });
  });
});
```

## Continuous Improvement

### Test Maintenance
1. **Update tests when UI changes** - Keep tests in sync with components
2. **Remove obsolete tests** - Delete tests for removed features
3. **Refactor test utilities** - Extract common patterns
4. **Monitor test performance** - Keep tests fast

### Red Flags in Frontend Tests
- Tests that break when changing CSS classes
- Tests with hardcoded timeouts over 1000ms
- Tests that directly check component state
- Tests with more than 10 assertions
- Tests that require specific render order

### Testing Checklist
- [ ] Can a user actually do this?
- [ ] Will this test break if I refactor?
- [ ] Is this testing my code or the framework?
- [ ] Would this test catch real bugs?

Remember: **Frontend tests should verify what users see and do, not how components work internally.**