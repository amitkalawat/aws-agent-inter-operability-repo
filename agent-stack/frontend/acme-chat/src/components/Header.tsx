import React from 'react';
import { User } from '../services/AuthService';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="app-title">
            🚀 Agent Interoperability Demo
          </h1>
          <span className="app-subtitle">
            Powered by Amazon Bedrock AgentCore
          </span>
        </div>

        <div className="header-center">
          {user && (
            <div className="dashboard-buttons">
              <button 
                className="dashboard-button"
                onClick={() => window.open('https://d22um2piuwyb63.cloudfront.net/', '_blank')}
                title="Access Video Telemetry Dashboard"
              >
                📊 Video Telemetry Dashboard
              </button>
              <button 
                className="dashboard-button"
                onClick={() => window.open('https://d1zugwkd4hiwal.cloudfront.net/login', '_blank')}
                title="Access MCP Registry"
              >
                🔧 MCP Registry
              </button>
            </div>
          )}
        </div>

        <div className="header-right">
          {user && (
            <div className="user-info">
              <div className="user-details">
                <span className="user-name">Welcome, {user.email}</span>
                <span className="user-status">🟢 Authenticated</span>
              </div>
              <button 
                className="logout-button"
                onClick={onLogout}
                title="Sign out"
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;