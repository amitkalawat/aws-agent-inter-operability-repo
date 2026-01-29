import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ToolsList } from '../components/ToolsList';
import { RegistryService } from '../services/RegistryService';
import { McpServer, McpTool } from '../types';

const categoryLabels: Record<string, string> = {
  documentation: 'Documentation',
  data: 'Data & Analytics',
  vision: 'Vision',
  generation: 'Generation',
  other: 'Other',
};

export const ServerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [server, setServer] = useState<McpServer | null>(null);
  const [tools, setTools] = useState<McpTool[]>([]);
  const [toolsUpdatedAt, setToolsUpdatedAt] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (id) {
      loadServer(id);
    }
  }, [id]);

  const loadServer = async (serverId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await RegistryService.getServer(serverId);
      setServer(data);
      setTools(data.tools || []);
      setToolsUpdatedAt(data.toolsUpdatedAt);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load server');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshTools = async () => {
    if (!id) return;
    setToolsLoading(true);
    try {
      const result = await RegistryService.getTools(id, true);
      setTools(result.tools);
      setToolsUpdatedAt(result.toolsUpdatedAt);
    } catch (err) {
      console.error('Failed to refresh tools:', err);
    } finally {
      setToolsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!id || !server) return;
    if (!window.confirm(`Are you sure you want to delete "${server.name}"?`)) {
      return;
    }
    setDeleting(true);
    try {
      await RegistryService.deleteServer(id);
      navigate('/');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete server');
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>
          <div style={styles.spinner}></div>
          Loading server details...
        </div>
      </div>
    );
  }

  if (error || !server) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          {error || 'Server not found'}
          <Link to="/" style={styles.backLink}>
            &larr; Back to Registry
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <Link to="/" style={styles.backLink}>
        &larr; Back to Registry
      </Link>

      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.badges}>
            <span style={styles.categoryBadge}>
              {categoryLabels[server.category] || server.category}
            </span>
            <span
              style={{
                ...styles.statusBadge,
                backgroundColor:
                  server.status === 'active' ? '#e8f5e9' : '#ffebee',
                color: server.status === 'active' ? '#2e7d32' : '#c62828',
              }}
            >
              {server.status}
            </span>
          </div>
          <h1 style={styles.title}>{server.name}</h1>
          <p style={styles.description}>{server.description}</p>
        </div>

        <div style={styles.actions}>
          <button
            onClick={handleDelete}
            disabled={deleting}
            style={styles.deleteBtn}
          >
            {deleting ? 'Deleting...' : 'Delete Server'}
          </button>
        </div>
      </div>

      <div style={styles.details}>
        <div style={styles.detailCard}>
          <h3 style={styles.detailTitle}>Runtime ARN</h3>
          <code style={styles.arn}>{server.runtimeArn}</code>
        </div>

        <div style={styles.detailCard}>
          <h3 style={styles.detailTitle}>Tags</h3>
          <div style={styles.tags}>
            {server.tags.map((tag) => (
              <span key={tag} style={styles.tag}>
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div style={styles.detailCard}>
          <h3 style={styles.detailTitle}>Timestamps</h3>
          <div style={styles.timestamps}>
            <div>
              <span style={styles.timestampLabel}>Created:</span>
              <span>{new Date(server.createdAt).toLocaleString()}</span>
            </div>
            <div>
              <span style={styles.timestampLabel}>Updated:</span>
              <span>{new Date(server.updatedAt).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      <ToolsList
        tools={tools}
        loading={toolsLoading}
        onRefresh={handleRefreshTools}
        lastUpdated={toolsUpdatedAt}
      />
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '1000px',
    margin: '0 auto',
    padding: '24px',
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
    padding: '40px',
    borderRadius: '8px',
    textAlign: 'center',
  },
  backLink: {
    color: '#666',
    textDecoration: 'none',
    fontSize: '14px',
    display: 'inline-block',
    marginBottom: '20px',
  },
  header: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '24px',
    marginBottom: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerContent: {
    flex: 1,
  },
  badges: {
    display: 'flex',
    gap: '8px',
    marginBottom: '12px',
  },
  categoryBadge: {
    fontSize: '12px',
    fontWeight: '500',
    padding: '4px 8px',
    borderRadius: '4px',
    backgroundColor: '#e3f2fd',
    color: '#1976d2',
  },
  statusBadge: {
    fontSize: '11px',
    fontWeight: '500',
    padding: '4px 8px',
    borderRadius: '12px',
    textTransform: 'uppercase',
  },
  title: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#232f3e',
    marginBottom: '8px',
  },
  description: {
    fontSize: '16px',
    color: '#555',
    lineHeight: '1.6',
  },
  actions: {
    marginLeft: '24px',
  },
  deleteBtn: {
    padding: '10px 20px',
    fontSize: '14px',
    backgroundColor: '#ffebee',
    color: '#c62828',
    border: '1px solid #ef9a9a',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
  },
  details: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '16px',
    marginBottom: '20px',
  },
  detailCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '16px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  detailTitle: {
    fontSize: '13px',
    fontWeight: '600',
    color: '#888',
    textTransform: 'uppercase',
    marginBottom: '8px',
  },
  arn: {
    fontSize: '12px',
    color: '#333',
    backgroundColor: '#f5f5f5',
    padding: '8px',
    borderRadius: '4px',
    display: 'block',
    wordBreak: 'break-all',
  },
  tags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  tag: {
    fontSize: '12px',
    color: '#666',
    backgroundColor: '#f0f0f0',
    padding: '4px 8px',
    borderRadius: '4px',
  },
  timestamps: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    fontSize: '13px',
    color: '#555',
  },
  timestampLabel: {
    fontWeight: '500',
    marginRight: '8px',
  },
};
