import React, { useState, useEffect } from 'react';
import './App.css';
import AuthService, { User } from './services/AuthService';
import ChatInterface from './components/ChatInterface';
import Header from './components/Header';

// Login page component with Cognito OAuth button
const LoginPage: React.FC<{ onLogin: () => void; loading: boolean; error: string | null }> = ({
  onLogin,
  loading,
  error
}) => {
  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🚀 Agent Interoperability Demo</h1>
          <p className="subtitle">Powered by Amazon Bedrock AgentCore</p>
        </div>

        {error && (
          <div className="error-message">
            <p>⚠️ {error}</p>
          </div>
        )}

        <button
          className="login-button"
          onClick={onLogin}
          disabled={loading}
        >
          {loading ? 'Redirecting...' : 'Sign In with Cognito'}
        </button>

        <p className="login-hint">
          Click to sign in using AWS Cognito
        </p>
      </div>
    </div>
  );
};

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if this is an OAuth callback
    const handleAuth = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const errorParam = params.get('error');

      if (errorParam) {
        setError(params.get('error_description') || 'Authentication failed');
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
        setLoading(false);
        return;
      }

      if (code) {
        try {
          const authenticatedUser = await AuthService.handleCallback(code);
          setUser(authenticatedUser);
          // Clean URL after successful auth
          window.history.replaceState({}, document.title, window.location.pathname);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to complete login');
        }
        setLoading(false);
        return;
      }

      // No code in URL, check for existing session
      try {
        const currentUser = await AuthService.getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        console.error('Failed to get current user:', err);
      }
      setLoading(false);
    };

    handleAuth();
  }, []);

  useEffect(() => {
    // Add/remove login-page class to body for aurora background
    if (!user && !loading) {
      document.body.classList.add('login-page');
    } else {
      document.body.classList.remove('login-page');
    }

    // Cleanup on unmount
    return () => {
      document.body.classList.remove('login-page');
    };
  }, [user, loading]);

  const handleLogin = async () => {
    setError(null);
    setLoading(true);
    await AuthService.login();
    // This redirects to Cognito, so we won't reach here
  };

  const handleLogout = async () => {
    try {
      setError(null);
      await AuthService.signOut();
      // signOut redirects to Cognito logout, so we don't need setUser(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logout failed');
      console.error('Logout failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading Agent Interoperability Demo...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header user={user} onLogout={handleLogout} />

      <main className="main-content">
        {!user ? (
          <LoginPage onLogin={handleLogin} loading={loading} error={error} />
        ) : (
          <ChatInterface user={user} />
        )}
      </main>
    </div>
  );
}

export default App;
