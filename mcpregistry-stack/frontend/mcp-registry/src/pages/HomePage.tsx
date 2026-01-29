import React, { useState, useEffect } from 'react';
import { SearchBar } from '../components/SearchBar';
import { ServerCard } from '../components/ServerCard';
import { RegistryService } from '../services/RegistryService';
import { McpServer } from '../types';

export const HomePage: React.FC = () => {
  const [servers, setServers] = useState<McpServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('');

  const loadServers = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await RegistryService.listServers({
        category: category || undefined,
        search: searchQuery || undefined,
      });
      setServers(result.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load servers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServers();
  }, [category]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    loadServers();
  };

  return (
    <div style={styles.container}>
      <div style={styles.hero}>
        <h1 style={styles.title}>MCP Server Registry</h1>
        <p style={styles.subtitle}>
          Browse and manage MCP servers deployed on AWS Bedrock AgentCore
        </p>
      </div>

      <SearchBar
        onSearch={handleSearch}
        onCategoryChange={setCategory}
        selectedCategory={category}
      />

      {loading && (
        <div style={styles.loading}>
          <div style={styles.spinner}></div>
          Loading servers...
        </div>
      )}

      {error && (
        <div style={styles.error}>
          {error}
          <button onClick={loadServers} style={styles.retryBtn}>
            Retry
          </button>
        </div>
      )}

      {!loading && !error && servers.length === 0 && (
        <div style={styles.empty}>
          No MCP servers found. Try a different search or category.
        </div>
      )}

      {!loading && !error && servers.length > 0 && (
        <div style={styles.grid}>
          {servers.map((server) => (
            <ServerCard key={server.serverId} server={server} />
          ))}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '24px',
  },
  hero: {
    textAlign: 'center',
    marginBottom: '32px',
  },
  title: {
    fontSize: '32px',
    fontWeight: '700',
    color: '#232f3e',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '16px',
    color: '#666',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    padding: '60px',
    color: '#666',
    fontSize: '14px',
  },
  spinner: {
    width: '24px',
    height: '24px',
    border: '3px solid #ddd',
    borderTopColor: '#ff9900',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '20px',
    borderRadius: '8px',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
  },
  retryBtn: {
    padding: '8px 16px',
    fontSize: '13px',
    backgroundColor: '#c62828',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  empty: {
    padding: '60px',
    textAlign: 'center',
    color: '#888',
    fontSize: '16px',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
    gap: '20px',
  },
};
