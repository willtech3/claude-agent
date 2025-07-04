# CLAUDE.md - Frontend Code Quality Guidelines

## Inheritance
- **Extends:** /CLAUDE.md (root)
- **Overrides:** None (CRITICAL RULES cannot be overridden)
- **Scope:** All JavaScript/TypeScript code in frontend/src

## Rules

**Context:** Load this document when implementing frontend features, reviewing React code, or making architectural decisions for the Jules-inspired UI.

---

# Frontend Code Quality Guidelines for Claude Agent

This document outlines practical code quality standards for our Next.js frontend with Jules-inspired design. We prioritize user experience, performance, and maintainability.

## Core Philosophy

> "The best code is no code. The best UI is no UI. When you must have either, make them invisible."

1. **User Experience First** - Every decision should improve UX
2. **Performance by Default** - Fast interactions, smooth animations
3. **Accessibility Always** - Inclusive design is good design
4. **Simple over Clever** - Readable code beats smart code
5. **Composition over Complexity** - Build with small, focused components

## Clean Code Principles (React/TypeScript)

### 1. Component Design

```typescript
// ✅ GOOD: Focused component with clear props
interface TaskCardProps {
  task: Task;
  onStatusChange?: (taskId: string, status: TaskStatus) => void;
  isSelected?: boolean;
}

export function TaskCard({ task, onStatusChange, isSelected = false }: TaskCardProps) {
  return (
    <Card className={cn("task-card", isSelected && "task-card--selected")}>
      <CardHeader>
        <h3>{task.title}</h3>
        <TaskStatus status={task.status} />
      </CardHeader>
      <CardBody>
        <p>{task.description}</p>
      </CardBody>
    </Card>
  );
}

// ❌ BAD: Kitchen sink component
export function TaskManager() {
  // 500 lines of mixed concerns: API calls, state, UI, business logic
  const [tasks, setTasks] = useState([]);
  const [filters, setFilters] = useState({});
  const [user, setUser] = useState(null);
  // ... everything in one component
}
```

### 2. Custom Hooks Pattern

```typescript
// ✅ GOOD: Reusable, focused hook
function useWebSocket(url: string) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [lastMessage, setLastMessage] = useState<any>(null);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => setStatus('connected');
    ws.onmessage = (event) => setLastMessage(JSON.parse(event.data));
    ws.onclose = () => setStatus('disconnected');
    
    return () => ws.close();
  }, [url]);
  
  return { status, lastMessage };
}

// Usage is clean
function AgentOutput({ taskId }: { taskId: string }) {
  const { status, lastMessage } = useWebSocket(`/ws/${taskId}`);
  
  if (status === 'connecting') return <Spinner />;
  // ...
}

// ❌ BAD: Business logic in components
function AgentOutput({ taskId }: { taskId: string }) {
  const [ws, setWs] = useState(null);
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    const websocket = new WebSocket(`/ws/${taskId}`);
    setWs(websocket);
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'output') {
        setMessages(prev => [...prev, data]);
      }
      // ... lots of logic in component
    };
  }, []);
}
```

### 3. State Management

```typescript
// ✅ GOOD: Colocate state close to usage
function TaskList() {
  // Local state for UI concerns
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  
  // Server state with React Query
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks
  });
  
  return (
    <div>
      {tasks?.map(task => (
        <TaskCard
          key={task.id}
          task={task}
          isSelected={task.id === selectedTaskId}
          onClick={() => setSelectedTaskId(task.id)}
        />
      ))}
    </div>
  );
}

// ❌ BAD: Global state for everything
// store.ts
export const globalStore = {
  tasks: [],
  selectedTaskId: null,
  user: null,
  theme: 'light',
  // Everything in global state
};
```

### 4. Type Safety

```typescript
// ✅ GOOD: Strict types, no any
interface TaskMessage {
  type: 'output' | 'error' | 'complete';
  content: string;
  timestamp: string;
}

function processMessage(message: TaskMessage): void {
  switch (message.type) {
    case 'output':
      console.log(`Output: ${message.content}`);
      break;
    case 'error':
      console.error(`Error: ${message.content}`);
      break;
    case 'complete':
      console.log('Task completed');
      break;
    // TypeScript ensures exhaustive handling
  }
}

// ❌ BAD: Loose types, any usage
function processMessage(message: any) {
  if (message.type === 'output') {
    // No type safety
  }
}
```

## Jules-Inspired Design Patterns

### 1. Minimal UI Components

```typescript
// ✅ GOOD: Clean, focused design
export function TaskStatus({ status }: { status: TaskStatus }) {
  return (
    <div className="flex items-center gap-2">
      <StatusIcon status={status} />
      <span className="text-sm text-gray-600">
        {statusLabels[status]}
      </span>
    </div>
  );
}

// ❌ BAD: Over-designed component
export function TaskStatus({ status, size, variant, showIcon, showLabel, animated, color }) {
  // Too many options, too complex
}
```

### 2. Smooth Interactions

```typescript
// ✅ GOOD: Thoughtful animations
import { motion } from 'framer-motion';

export function SlidePanel({ isOpen, children }: SlidePanelProps) {
  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: isOpen ? 0 : '100%' }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="slide-panel"
    >
      {children}
    </motion.div>
  );
}

// ❌ BAD: Jarring transitions
export function Panel({ isOpen, children }) {
  return (
    <div style={{ display: isOpen ? 'block' : 'none' }}>
      {children}
    </div>
  );
}
```

### 3. Information Hierarchy

```typescript
// ✅ GOOD: Clear visual hierarchy
export function TaskTimeline({ events }: { events: TimelineEvent[] }) {
  return (
    <div className="space-y-4">
      {events.map((event, index) => (
        <div key={event.id} className="flex gap-4">
          <div className="flex flex-col items-center">
            <TimelineIcon type={event.type} />
            {index < events.length - 1 && (
              <div className="w-0.5 h-full bg-gray-200" />
            )}
          </div>
          <div className="flex-1 pb-4">
            <h4 className="font-medium">{event.title}</h4>
            <p className="text-sm text-gray-600">{event.description}</p>
            <time className="text-xs text-gray-400">
              {formatRelativeTime(event.timestamp)}
            </time>
          </div>
        </div>
      ))}
    </div>
  );
}
```

## Performance Patterns

### 1. Code Splitting

```typescript
// ✅ GOOD: Lazy load heavy components
const CodeEditor = lazy(() => import('./CodeEditor'));
const DiffViewer = lazy(() => import('./DiffViewer'));

export function TaskDetails({ task }: { task: Task }) {
  return (
    <Suspense fallback={<Skeleton />}>
      {task.hasCode && <CodeEditor code={task.code} />}
      {task.hasDiff && <DiffViewer diff={task.diff} />}
    </Suspense>
  );
}

// ❌ BAD: Import everything upfront
import CodeMirror from 'codemirror';  // 2MB
import DiffMatchPatch from 'diff-match-patch';  // 500KB
// Even if user never views code
```

### 2. Optimistic Updates

```typescript
// ✅ GOOD: Immediate feedback
function TaskActions({ task }: { task: Task }) {
  const queryClient = useQueryClient();
  const updateStatus = useMutation({
    mutationFn: (status: TaskStatus) => 
      updateTaskStatus(task.id, status),
    onMutate: async (newStatus) => {
      // Cancel in-flight queries
      await queryClient.cancelQueries(['task', task.id]);
      
      // Optimistically update
      queryClient.setQueryData(['task', task.id], (old: Task) => ({
        ...old,
        status: newStatus
      }));
      
      return { previousTask: task };
    },
    onError: (err, newStatus, context) => {
      // Rollback on error
      queryClient.setQueryData(
        ['task', task.id], 
        context.previousTask
      );
    }
  });
  
  return (
    <Button onClick={() => updateStatus.mutate('completed')}>
      Complete Task
    </Button>
  );
}

// ❌ BAD: Wait for server response
function TaskActions({ task }) {
  const [isUpdating, setIsUpdating] = useState(false);
  
  const handleComplete = async () => {
    setIsUpdating(true);
    await fetch(`/api/tasks/${task.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: 'completed' })
    });
    setIsUpdating(false);
    // User waits...
  };
}
```

### 3. Virtual Scrolling

```typescript
// ✅ GOOD: Virtualize long lists
import { FixedSizeList } from 'react-window';

export function FileList({ files }: { files: File[] }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <FileItem file={files[index]} />
    </div>
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={files.length}
      itemSize={35}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}

// ❌ BAD: Render thousands of DOM nodes
export function FileList({ files }) {
  return (
    <div>
      {files.map(file => (
        <FileItem key={file.path} file={file} />
      ))}
    </div>
  );
}
```

## Accessibility Patterns

### 1. Keyboard Navigation

```typescript
// ✅ GOOD: Full keyboard support
export function CommandPalette() {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [commands, setCommands] = useState<Command[]>([]);
  
  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(i => Math.min(i + 1, commands.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(i => Math.max(i - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        commands[selectedIndex]?.execute();
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  };
  
  return (
    <div role="dialog" aria-label="Command palette" onKeyDown={handleKeyDown}>
      {/* ... */}
    </div>
  );
}
```

### 2. Screen Reader Support

```typescript
// ✅ GOOD: Proper ARIA labels
export function TaskProgress({ task }: { task: Task }) {
  const percentage = (task.completed / task.total) * 100;
  
  return (
    <div
      role="progressbar"
      aria-valuenow={percentage}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Task progress: ${percentage.toFixed(0)}% complete`}
    >
      <div 
        className="progress-bar"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

// ❌ BAD: No accessibility
export function TaskProgress({ task }) {
  return (
    <div className="progress">
      <div style={{ width: `${task.progress}%` }} />
    </div>
  );
}
```

## Error Handling

### 1. Error Boundaries

```typescript
// ✅ GOOD: Graceful error handling
export class TaskErrorBoundary extends Component<Props, State> {
  state = { hasError: false };
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logger.error('Task component error', { error, errorInfo });
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          message="Unable to load task"
          onRetry={() => this.setState({ hasError: false })}
        />
      );
    }
    
    return this.props.children;
  }
}
```

### 2. User-Friendly Errors

```typescript
// ✅ GOOD: Helpful error messages
export function useTask(taskId: string) {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => fetchTask(taskId),
    retry: 3,
    onError: (error) => {
      if (error.response?.status === 404) {
        toast.error('Task not found. It may have been deleted.');
      } else if (error.response?.status === 403) {
        toast.error('You don\'t have permission to view this task.');
      } else {
        toast.error('Unable to load task. Please try again.');
      }
    }
  });
}

// ❌ BAD: Technical errors shown to users
catch (error) {
  alert(`Error: ${error.stack}`);  // Users don't need stack traces
}
```

## Code Organization

### File Structure
```
frontend/src/
├── components/        # Reusable UI components
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── index.ts
├── features/         # Feature-specific components
│   ├── tasks/
│   │   ├── TaskList/
│   │   ├── TaskDetail/
│   │   └── hooks/
├── lib/             # Utilities and helpers
│   ├── api.ts
│   ├── utils.ts
│   └── constants.ts
├── styles/          # Global styles and design tokens
│   ├── globals.css
│   └── tokens.ts
└── types/           # TypeScript types
    └── index.ts
```

### Barrel Exports
```typescript
// ✅ GOOD: Clean imports via index files
// components/Button/index.ts
export { Button } from './Button';
export type { ButtonProps } from './Button';

// Usage
import { Button } from '@/components/Button';

// ❌ BAD: Deep imports
import { Button } from '@/components/Button/Button';
```

## Anti-Patterns to Avoid

### 1. useEffect Overuse
```typescript
// ❌ BAD: Effect for derived state
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// ✅ GOOD: Compute during render
const fullName = `${firstName} ${lastName}`;
```

### 2. Prop Drilling
```typescript
// ❌ BAD: Passing props through many levels
<App user={user}>
  <Layout user={user}>
    <Header user={user}>
      <UserMenu user={user} />
    </Header>
  </Layout>
</App>

// ✅ GOOD: Use context for cross-cutting concerns
const UserContext = createContext<User | null>(null);

export function UserProvider({ children }) {
  const user = useUser();
  return (
    <UserContext.Provider value={user}>
      {children}
    </UserContext.Provider>
  );
}
```

### 3. Premature Optimization
```typescript
// ❌ BAD: useMemo/useCallback everywhere
const handleClick = useCallback(() => {
  console.log('clicked');
}, []);  // No dependencies, unnecessary

const style = useMemo(() => ({
  color: 'blue'
}), []);  // Static object, unnecessary

// ✅ GOOD: Optimize when measured
const expensiveComputation = useMemo(() => 
  calculateComplexValue(data),
  [data]
);  // Actually expensive, worth memoizing
```

## Code Review Checklist

Before submitting code, verify:

- [ ] **Accessibility**: Keyboard navigable, screen reader friendly
- [ ] **Performance**: No unnecessary rerenders, lazy loading used
- [ ] **Type Safety**: No `any` types, strict null checks
- [ ] **Error Handling**: User-friendly error messages
- [ ] **Component Focus**: Single responsibility components
- [ ] **Clean Imports**: Using barrel exports, no circular deps
- [ ] **Responsive**: Works on mobile and desktop
- [ ] **Dark Mode**: Respects theme preferences

## Examples: Refactoring for Quality

### Before: Monolithic Component
```tsx
function TaskPage() {
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ws, setWs] = useState(null);
  const [output, setOutput] = useState([]);
  
  useEffect(() => {
    // Fetch task
    fetch(`/api/tasks/${id}`)
      .then(res => res.json())
      .then(setTask)
      .catch(setError)
      .finally(() => setLoading(false));
    
    // Setup WebSocket
    const websocket = new WebSocket(`/ws/${id}`);
    websocket.onmessage = (e) => {
      setOutput(prev => [...prev, e.data]);
    };
    setWs(websocket);
    
    return () => websocket.close();
  }, [id]);
  
  // 200+ lines of mixed UI...
}
```

### After: Composed Components
```tsx
function TaskPage({ taskId }: { taskId: string }) {
  return (
    <TaskProvider taskId={taskId}>
      <div className="task-page">
        <TaskHeader />
        <div className="task-content">
          <TaskDetails />
          <AgentOutput />
        </div>
        <TaskActions />
      </div>
    </TaskProvider>
  );
}

function TaskHeader() {
  const { task } = useTaskContext();
  return (
    <header className="task-header">
      <h1>{task.title}</h1>
      <TaskStatus status={task.status} />
    </header>
  );
}

function AgentOutput() {
  const { taskId } = useTaskContext();
  const { messages } = useTaskWebSocket(taskId);
  
  return (
    <OutputPanel>
      {messages.map(msg => (
        <OutputLine key={msg.id} message={msg} />
      ))}
    </OutputPanel>
  );
}
```

## Conclusion

Good frontend code should:
- **Delight Users** - Fast, smooth, accessible
- **Scale Gracefully** - Components compose well
- **Maintain Easily** - Clear patterns, good types
- **Perform Well** - Optimized for real usage
- **Handle Errors** - Graceful degradation

Remember: We're building a Jules-inspired interface. Every line of code should contribute to a clean, focused, and delightful user experience.