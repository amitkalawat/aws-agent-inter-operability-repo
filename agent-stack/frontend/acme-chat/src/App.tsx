import React, { useState, useEffect } from 'react';
import './App.css';
import AuthService, { User } from './services/AuthService';
import LoginForm from './components/LoginForm';
import ChatInterface from './components/ChatInterface';
import Header from './components/Header';

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is already authenticated on app start
    checkAuthStatus();
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

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const currentUser = await AuthService.getCurrentUser();
      setUser(currentUser);
    } catch (error: any) {
      console.error('Failed to get current user:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (username: string, password: string) => {
    try {
      setError(null);
      setLoading(true);
      const authenticatedUser = await AuthService.signIn(username, password);
      setUser(authenticatedUser);
    } catch (error: any) {
      setError(error.message);
      console.error('Login failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      setError(null);
      await AuthService.signOut();
      setUser(null);
    } catch (error: any) {
      setError(error.message);
      console.error('Logout failed:', error);
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
        {error && (
          <div className="error-banner">
            <p>⚠️ {error}</p>
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {!user ? (
          <LoginForm onLogin={handleLogin} loading={loading} />
        ) : (
          <ChatInterface user={user} />
        )}
      </main>
    </div>
  );
}

export default App;
