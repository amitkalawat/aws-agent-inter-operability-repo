import React from 'react';
import { Link } from 'react-router-dom';

interface HeaderUser {
  username: string;
  email?: string;
}

interface HeaderProps {
  user: HeaderUser | null;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  return (
    <header style={styles.header}>
      <div style={styles.container}>
        <Link to="/" style={styles.logo}>
          <span style={styles.logoIcon}>&#9881;</span>
          MCP Registry
        </Link>

        <nav style={styles.nav}>
          <Link to="/" style={styles.navLink}>
            Browse
          </Link>
          <Link to="/register" style={styles.navLink}>
            Register
          </Link>
        </nav>

        <div style={styles.userSection}>
          {user && (
            <>
              <span style={styles.username}>{user.username}</span>
              <button onClick={onLogout} style={styles.logoutBtn}>
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

const styles: Record<string, React.CSSProperties> = {
  header: {
    backgroundColor: '#232f3e',
    color: 'white',
    padding: '0 20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '60px',
  },
  logo: {
    color: 'white',
    textDecoration: 'none',
    fontSize: '20px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  logoIcon: {
    fontSize: '24px',
  },
  nav: {
    display: 'flex',
    gap: '24px',
  },
  navLink: {
    color: '#aab7c4',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'color 0.2s',
  },
  userSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  username: {
    fontSize: '14px',
    color: '#aab7c4',
  },
  logoutBtn: {
    background: 'transparent',
    border: '1px solid #aab7c4',
    color: '#aab7c4',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
};
