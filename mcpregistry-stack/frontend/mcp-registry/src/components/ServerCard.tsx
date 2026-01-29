import React from 'react';
import { Link } from 'react-router-dom';
import { McpServer } from '../types';

interface ServerCardProps {
  server: McpServer;
}

const categoryColors: Record<string, string> = {
  documentation: '#2196f3',
  data: '#4caf50',
  vision: '#9c27b0',
  generation: '#ff9800',
  other: '#607d8b',
};

const categoryLabels: Record<string, string> = {
  documentation: 'Documentation',
  data: 'Data & Analytics',
  vision: 'Vision',
  generation: 'Generation',
  other: 'Other',
};

export const ServerCard: React.FC<ServerCardProps> = ({ server }) => {
  const categoryColor = categoryColors[server.category] || categoryColors.other;

  return (
    <Link to={`/servers/${server.serverId}`} style={styles.card}>
      <div style={styles.header}>
        <span
          style={{
            ...styles.category,
            backgroundColor: `${categoryColor}20`,
            color: categoryColor,
          }}
        >
          {categoryLabels[server.category] || server.category}
        </span>
        <span
          style={{
            ...styles.status,
            backgroundColor: server.status === 'active' ? '#e8f5e9' : '#ffebee',
            color: server.status === 'active' ? '#2e7d32' : '#c62828',
          }}
        >
          {server.status}
        </span>
      </div>

      <h3 style={styles.name}>{server.name}</h3>
      <p style={styles.description}>{server.description}</p>

      <div style={styles.tags}>
        {server.tags.slice(0, 4).map((tag) => (
          <span key={tag} style={styles.tag}>
            {tag}
          </span>
        ))}
        {server.tags.length > 4 && (
          <span style={styles.moreTag}>+{server.tags.length - 4}</span>
        )}
      </div>

      <div style={styles.footer}>
        <span style={styles.toolCount}>
          {server.tools?.length || 0} tools
        </span>
        <span style={styles.viewLink}>View Details &rarr;</span>
      </div>
    </Link>
  );
};

const styles: Record<string, React.CSSProperties> = {
  card: {
    display: 'block',
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '20px',
    textDecoration: 'none',
    color: 'inherit',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    transition: 'box-shadow 0.2s, transform 0.2s',
    cursor: 'pointer',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  category: {
    fontSize: '12px',
    fontWeight: '500',
    padding: '4px 8px',
    borderRadius: '4px',
  },
  status: {
    fontSize: '11px',
    fontWeight: '500',
    padding: '3px 8px',
    borderRadius: '12px',
    textTransform: 'uppercase',
  },
  name: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#232f3e',
    marginBottom: '8px',
  },
  description: {
    fontSize: '14px',
    color: '#666',
    lineHeight: '1.5',
    marginBottom: '16px',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  tags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    marginBottom: '16px',
  },
  tag: {
    fontSize: '12px',
    color: '#666',
    backgroundColor: '#f0f0f0',
    padding: '4px 8px',
    borderRadius: '4px',
  },
  moreTag: {
    fontSize: '12px',
    color: '#999',
    padding: '4px 8px',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: '12px',
    borderTop: '1px solid #eee',
  },
  toolCount: {
    fontSize: '13px',
    color: '#888',
  },
  viewLink: {
    fontSize: '13px',
    color: '#ff9900',
    fontWeight: '500',
  },
};
