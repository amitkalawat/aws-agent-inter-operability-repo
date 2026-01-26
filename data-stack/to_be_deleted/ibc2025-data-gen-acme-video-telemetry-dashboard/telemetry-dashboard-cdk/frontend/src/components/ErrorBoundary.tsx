import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { 
      hasError: true,
      error,
      errorInfo: null
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '20px',
          margin: '20px',
          border: '2px solid #ff0000',
          borderRadius: '5px',
          backgroundColor: '#fff5f5',
          color: '#333'
        }}>
          <h2 style={{ color: '#ff0000' }}>Something went wrong!</h2>
          <details style={{ whiteSpace: 'pre-wrap', marginTop: '10px' }}>
            <summary>Error Details (click to expand)</summary>
            <p><strong>Error:</strong> {this.state.error && this.state.error.toString()}</p>
            <p><strong>Stack:</strong></p>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '10px', 
              borderRadius: '3px',
              overflow: 'auto',
              fontSize: '12px'
            }}>
              {this.state.error?.stack}
            </pre>
            {this.state.errorInfo && (
              <>
                <p><strong>Component Stack:</strong></p>
                <pre style={{ 
                  backgroundColor: '#f5f5f5', 
                  padding: '10px', 
                  borderRadius: '3px',
                  overflow: 'auto',
                  fontSize: '12px'
                }}>
                  {this.state.errorInfo.componentStack}
                </pre>
              </>
            )}
          </details>
          <button 
            onClick={this.handleReset}
            style={{
              marginTop: '15px',
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              cursor: 'pointer'
            }}
          >
            Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;