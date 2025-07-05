import { useState, useCallback, useRef, useEffect } from 'react';
import api from '@/lib/api';

type Status = 'idle' | 'submitting' | 'connecting' | 'processing' | 'complete' | 'error';

interface OutputMessage {
  type: 'output' | 'error' | 'complete';
  content: string;
  timestamp: string;
}

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [output, setOutput] = useState<OutputMessage[]>([]);
  const [status, setStatus] = useState<Status>('idle');
  const [taskId, setTaskId] = useState<string | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = useCallback((taskId: string) => {
    setStatus('connecting');
    
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001';
    const ws = new WebSocket(`${wsUrl}/ws/${taskId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('processing');
      setOutput(prev => [...prev, {
        type: 'output',
        content: 'Connected to agent...',
        timestamp: new Date().toISOString()
      }]);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'output':
            setOutput(prev => [...prev, {
              type: 'output',
              content: message.content,
              timestamp: message.timestamp || new Date().toISOString()
            }]);
            break;
          case 'complete':
            setStatus('complete');
            setOutput(prev => [...prev, {
              type: 'complete',
              content: 'Task completed successfully',
              timestamp: new Date().toISOString()
            }]);
            ws.close();
            break;
          case 'error':
            setStatus('error');
            setOutput(prev => [...prev, {
              type: 'error',
              content: message.content || 'An error occurred',
              timestamp: new Date().toISOString()
            }]);
            break;
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    ws.onerror = (error) => {
      setStatus('error');
      setOutput(prev => [...prev, {
        type: 'error',
        content: 'WebSocket connection error',
        timestamp: new Date().toISOString()
      }]);
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      wsRef.current = null;
      if (status === 'processing' || status === 'connecting') {
        setStatus('error');
        setOutput(prev => [...prev, {
          type: 'error',
          content: 'Connection closed unexpectedly',
          timestamp: new Date().toISOString()
        }]);
      }
    };
  }, [status]);

  const submitTask = async () => {
    if (!prompt.trim() || status !== 'idle') return;

    setStatus('submitting');
    setOutput([]);
    setTaskId(null);

    try {
      const response = await api.createTask({
        prompt: prompt.trim(),
        type: 'claude_code'
      });

      setTaskId(response.id);
      connectWebSocket(response.id);
    } catch (error) {
      setStatus('error');
      setOutput([{
        type: 'error',
        content: error instanceof Error ? error.message : 'Failed to submit task',
        timestamp: new Date().toISOString()
      }]);
    }
  };

  const resetTask = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setStatus('idle');
    setPrompt('');
    setOutput([]);
    setTaskId(null);
  };

  const getStatusColor = () => {
    switch (status) {
      case 'idle': return '#666';
      case 'submitting':
      case 'connecting':
      case 'processing': return '#0066cc';
      case 'complete': return '#00aa00';
      case 'error': return '#cc0000';
      default: return '#666';
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ border: '1px solid #ccc', padding: '20px', marginBottom: '20px' }}>
        <h1 style={{ margin: '0 0 20px 0', fontSize: '24px' }}>Claude Agent POC</h1>
        
        <div style={{ marginBottom: '10px' }}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter task..."
            disabled={status !== 'idle'}
            style={{
              width: '100%',
              height: '100px',
              fontFamily: 'monospace',
              fontSize: '14px',
              padding: '10px',
              border: '1px solid #ccc',
              resize: 'vertical'
            }}
          />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <button
            onClick={submitTask}
            disabled={status !== 'idle' || !prompt.trim()}
            style={{
              padding: '8px 16px',
              fontFamily: 'monospace',
              fontSize: '14px',
              cursor: status !== 'idle' || !prompt.trim() ? 'not-allowed' : 'pointer',
              opacity: status !== 'idle' || !prompt.trim() ? 0.5 : 1
            }}
          >
            Submit Task
          </button>
          
          {status !== 'idle' && (
            <button
              onClick={resetTask}
              style={{
                padding: '8px 16px',
                fontFamily: 'monospace',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Reset
            </button>
          )}
          
          <span style={{ color: getStatusColor(), fontWeight: 'bold' }}>
            Status: {status}
          </span>
          
          {taskId && (
            <span style={{ color: '#666', fontSize: '12px' }}>
              Task ID: {taskId}
            </span>
          )}
        </div>
      </div>
      
      <div style={{ border: '1px solid #ccc', padding: '10px' }}>
        <div style={{ marginBottom: '10px', fontWeight: 'bold' }}>Output:</div>
        <div
          ref={outputRef}
          style={{
            backgroundColor: '#f0f0f0',
            padding: '10px',
            height: '400px',
            overflowY: 'auto',
            fontFamily: 'monospace',
            fontSize: '13px',
            lineHeight: '1.5'
          }}
        >
          {output.length === 0 ? (
            <div style={{ color: '#666' }}>Waiting for output...</div>
          ) : (
            output.map((msg, index) => (
              <div
                key={index}
                style={{
                  color: msg.type === 'error' ? '#cc0000' : '#333',
                  marginBottom: '4px'
                }}
              >
                {msg.type === 'output' && '> '}
                {msg.type === 'error' && '! '}
                {msg.type === 'complete' && '✓ '}
                {msg.content}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}