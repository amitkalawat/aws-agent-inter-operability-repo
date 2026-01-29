import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Header } from './components/Header';
import { LoginForm } from './components/LoginForm';
import { HomePage } from './pages/HomePage';
import { ServerDetailPage } from './pages/ServerDetailPage';
import { RegisterPage } from './pages/RegisterPage';
import { AuthService, User } from './services/AuthService';

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
    setUser(null);
  };

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner}></div>
        Loading...
      </div>
    );
  }

  if (!user) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <BrowserRouter>
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
};

export default App;
