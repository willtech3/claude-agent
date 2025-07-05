import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }

      // Default error UI
      return (
        <div style={{
          padding: '20px',
          fontFamily: 'monospace',
          border: '1px solid #cc0000',
          backgroundColor: '#fff5f5',
          borderRadius: '4px',
          margin: '20px'
        }}>
          <h2 style={{ color: '#cc0000', marginTop: 0 }}>Something went wrong</h2>
          <p style={{ color: '#666' }}>{this.state.error.message}</p>
          <button
            onClick={this.reset}
            style={{
              padding: '8px 16px',
              fontFamily: 'monospace',
              fontSize: '14px',
              cursor: 'pointer',
              backgroundColor: '#cc0000',
              color: 'white',
              border: 'none',
              borderRadius: '4px'
            }}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}