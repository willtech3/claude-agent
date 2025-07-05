import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Home from '../index';

// Mock the API module
jest.mock('@/lib/api', () => ({
  createTask: jest.fn(),
}));

// Mock WebSocket
class MockWebSocket {
  url: string;
  readyState: number = 0;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    this.readyState = 0;
    setTimeout(() => {
      this.readyState = 1;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string) {
    // Mock implementation
  }

  close() {
    this.readyState = 3;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

// Replace global WebSocket
(global as any).WebSocket = MockWebSocket;

describe('Home', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the main page elements', () => {
    render(<Home />);
    
    // Check title
    expect(screen.getByText('Claude Agent POC')).toBeInTheDocument();
    
    // Check textarea
    const textarea = screen.getByPlaceholderText('Enter task...');
    expect(textarea).toBeInTheDocument();
    
    // Check submit button
    const submitButton = screen.getByText('Submit Task');
    expect(submitButton).toBeInTheDocument();
    
    // Check initial status
    expect(screen.getByText('Status: idle')).toBeInTheDocument();
    
    // Check output area
    expect(screen.getByText('Output:')).toBeInTheDocument();
    expect(screen.getByText('Waiting for output...')).toBeInTheDocument();
  });

  it('enables submit button when text is entered', () => {
    render(<Home />);
    
    const textarea = screen.getByPlaceholderText('Enter task...');
    const submitButton = screen.getByText('Submit Task');
    
    // Initially disabled
    expect(submitButton).toBeDisabled();
    
    // Type in textarea
    fireEvent.change(textarea, { target: { value: 'Test task' } });
    
    // Should be enabled
    expect(submitButton).not.toBeDisabled();
  });

  it('shows reset button when status is not idle', async () => {
    const mockApi = require('@/lib/api');
    mockApi.createTask.mockResolvedValue({ id: 'test-123' });
    
    render(<Home />);
    
    // No reset button initially
    expect(screen.queryByText('Reset')).not.toBeInTheDocument();
    
    // Enter text and submit
    const textarea = screen.getByPlaceholderText('Enter task...');
    fireEvent.change(textarea, { target: { value: 'Test task' } });
    
    const submitButton = screen.getByText('Submit Task');
    fireEvent.click(submitButton);
    
    // Wait for status change
    await waitFor(() => {
      expect(screen.getByText('Reset')).toBeInTheDocument();
    });
  });

  it('displays error message on API failure', async () => {
    const mockApi = require('@/lib/api');
    mockApi.createTask.mockRejectedValue(new Error('API Error'));
    
    render(<Home />);
    
    // Enter text and submit
    const textarea = screen.getByPlaceholderText('Enter task...');
    fireEvent.change(textarea, { target: { value: 'Test task' } });
    
    const submitButton = screen.getByText('Submit Task');
    fireEvent.click(submitButton);
    
    // Wait for error
    await waitFor(() => {
      expect(screen.getByText('! API Error')).toBeInTheDocument();
      expect(screen.getByText('Status: error')).toBeInTheDocument();
    });
  });

  it('disables form during submission', async () => {
    const mockApi = require('@/lib/api');
    mockApi.createTask.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ id: 'test-123' }), 100))
    );
    
    render(<Home />);
    
    // Enter text
    const textarea = screen.getByPlaceholderText('Enter task...');
    fireEvent.change(textarea, { target: { value: 'Test task' } });
    
    // Submit
    const submitButton = screen.getByText('Submit Task');
    fireEvent.click(submitButton);
    
    // Should be disabled during submission
    expect(textarea).toBeDisabled();
    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Status: submitting')).toBeInTheDocument();
  });

  it('handles WebSocket connection', async () => {
    const mockApi = require('@/lib/api');
    mockApi.createTask.mockResolvedValue({ id: 'test-123' });
    
    render(<Home />);
    
    // Submit task
    const textarea = screen.getByPlaceholderText('Enter task...');
    fireEvent.change(textarea, { target: { value: 'Test task' } });
    fireEvent.click(screen.getByText('Submit Task'));
    
    // Should show processing status after WebSocket connects
    await waitFor(() => {
      expect(screen.getByText('Status: processing')).toBeInTheDocument();
    });
  });
});

