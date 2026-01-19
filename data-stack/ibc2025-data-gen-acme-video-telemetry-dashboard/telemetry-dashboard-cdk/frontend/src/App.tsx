import React from 'react';
import { Amplify } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import Dashboard from './components/Dashboard';
import ErrorBoundary from './components/ErrorBoundary';
import { config } from './config';
import './App.css';

Amplify.configure({
  Auth: {
    region: config.region,
    userPoolId: config.userPoolId,
    userPoolWebClientId: config.userPoolWebClientId
  }
});

function App() {
  return (
    <div className="App">
      <ErrorBoundary>
        <Authenticator hideSignUp>
          {({ signOut, user }) => (
            <div className="app-container">
              <header className="app-header">
                <div className="header-content">
                  <h1>🎥 Video Telemetry Dashboard</h1>
                  <div className="header-info">
                    <span className="user-info">👤 {user?.username}</span>
                    <button onClick={signOut} className="sign-out-btn">Sign Out</button>
                  </div>
                </div>
              </header>
              <ErrorBoundary>
                <Dashboard />
              </ErrorBoundary>
            </div>
          )}
        </Authenticator>
      </ErrorBoundary>
    </div>
  );
}

export default App;