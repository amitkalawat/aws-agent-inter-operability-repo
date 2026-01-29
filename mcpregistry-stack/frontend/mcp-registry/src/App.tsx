import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Header } from './components/Header';
import { HomePage } from './pages/HomePage';
import { ServerDetailPage } from './pages/ServerDetailPage';
import { RegisterPage } from './pages/RegisterPage';
import { AuthService, User } from './services/AuthService';

// Callback handler component
const CallbackHandler: React.FC<{ onLogin: (user: User) => void }> = ({ onLogin }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(location.search);
      const code = params.get('code');
      const errorParam = params.get('error');

      if (errorParam) {
        setError(params.get('error_description') || 'Authentication failed');
        return;
      }

      if (code) {
        try {
          const user = await AuthService.handleCallback(code);
          onLogin(user);
          navigate('/', { replace: true });
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to complete login');
        }
      }
    };

    handleCallback();
  }, [location, navigate, onLogin]);

  if (error) {
    return (
      <div style={styles.loginContainer}>
        <div style={styles.loginBox}>
          <h1 style={styles.title}>Authentication Error</h1>
          <p style={styles.error}>{error}</p>
          <button style={styles.loginButton} onClick={() => AuthService.login()}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.loading}>
      <div style={styles.spinner}></div>
      Completing login...
    </div>
  );
};

// Login page component
const LoginPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
    await AuthService.login();
  };

  return (
    <div style={styles.loginContainer}>
      <div style={styles.loginBox}>
        <h1 style={styles.title}>MCP Registry</h1>
        <p style={styles.subtitle}>Sign in to access the registry</p>
        <button
          style={styles.loginButton}
          onClick={handleLogin}
          disabled={isLoading}
        >
          {isLoading ? 'Redirecting...' : 'Sign In with Cognito'}
        </button>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const currentUser = await AuthService.getCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (loggedInUser: User) => {
    setUser(loggedInUser);
  };

  const handleLogout = async () => {
    await AuthService.signOut();
    // signOut redirects to Cognito logout, so we don't need to setUser(null) here
  };

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner}></div>
        Loading...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* OAuth callback route - always accessible */}
        <Route path="/callback" element={<CallbackHandler onLogin={handleLogin} />} />

        {/* Protected routes */}
        {user ? (
          <Route path="*" element={
            <div style={styles.app}>
              <Header user={{ username: user.email, email: user.email }} onLogout={handleLogout} />
              <main style={styles.main}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/servers/:id" element={<ServerDetailPage />} />
                  <Route path="/register" element={<RegisterPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </main>
            </div>
          } />
        ) : (
          <Route path="*" element={<LoginPage />} />
        )}
      </Routes>
    </BrowserRouter>
  );
};

const styles: Record<string, React.CSSProperties> = {
  loading: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    color: '#666',
    fontSize: '16px',
  },
  spinner: {
    width: '24px',
    height: '24px',
    border: '3px solid #ddd',
    borderTopColor: '#ff9900',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  app: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  main: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loginContainer: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#232f3e',
  },
  loginBox: {
    backgroundColor: 'white',
    padding: '48px',
    borderRadius: '8px',
    textAlign: 'center' as const,
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    maxWidth: '400px',
    width: '90%',
  },
  title: {
    margin: '0 0 8px 0',
    color: '#232f3e',
    fontSize: '28px',
  },
  subtitle: {
    margin: '0 0 32px 0',
    color: '#666',
    fontSize: '16px',
  },
  loginButton: {
    width: '100%',
    padding: '14px 24px',
    backgroundColor: '#ff9900',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  error: {
    color: '#d32f2f',
    marginBottom: '24px',
  },
};

export default App;
