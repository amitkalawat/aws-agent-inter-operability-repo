import React, { useState } from 'react';
import { McpTool } from '../types';

interface ToolsListProps {
  tools: McpTool[];
  loading?: boolean;
  onRefresh?: () => void;
  lastUpdated?: string;
}

export const ToolsList: React.FC<ToolsListProps> = ({
  tools,
  loading,
  onRefresh,
  lastUpdated,
}) => {
  const [expandedTool, setExpandedTool] = useState<string | null>(null);

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'Never';
    return new Date(isoString).toLocaleString();
  };

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner}></div>
        Loading tools from MCP server...
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>
          Available Tools ({tools.length})
        </h3>
        <div style={styles.actions}>
          {lastUpdated && (
            <span style={styles.lastUpdated}>
              Last updated: {formatDate(lastUpdated)}
            </span>
          )}
          {onRefresh && (
            <button onClick={onRefresh} style={styles.refreshBtn}>
              Refresh Tools
            </button>
          )}
        </div>
      </div>

      {tools.length === 0 ? (
        <div style={styles.empty}>
          No tools available. Click "Refresh Tools" to fetch from the MCP server.
        </div>
      ) : (
        <div style={styles.toolsList}>
          {tools.map((tool) => (
            <div
              key={tool.name}
              style={styles.toolCard}
              onClick={() =>
                setExpandedTool(expandedTool === tool.name ? null : tool.name)
              }
            >
              <div style={styles.toolHeader}>
                <code style={styles.toolName}>{tool.name}</code>
                <span style={styles.expandIcon}>
                  {expandedTool === tool.name ? '▼' : '▶'}
                </span>
              </div>
              <p style={styles.toolDescription}>{tool.description}</p>

              {expandedTool === tool.name && tool.inputSchema && (
                <div style={styles.schemaSection}>
                  <h4 style={styles.schemaTitle}>Input Schema</h4>
                  <pre style={styles.schemaCode}>
                    {JSON.stringify(tool.inputSchema, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    flexWrap: 'wrap',
    gap: '12px',
  },
  title: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#232f3e',
    margin: 0,
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  lastUpdated: {
    fontSize: '13px',
    color: '#888',
  },
  refreshBtn: {
    padding: '8px 16px',
    fontSize: '13px',
    backgroundColor: '#ff9900',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    padding: '40px',
    color: '#666',
    fontSize: '14px',
  },
  spinner: {
    width: '20px',
    height: '20px',
    border: '2px solid #ddd',
    borderTopColor: '#ff9900',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  empty: {
    padding: '40px',
    textAlign: 'center',
    color: '#888',
    fontSize: '14px',
  },
  toolsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  toolCard: {
    border: '1px solid #e0e0e0',
    borderRadius: '6px',
    padding: '16px',
    cursor: 'pointer',
    transition: 'border-color 0.2s',
  },
  toolHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  toolName: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#2196f3',
    backgroundColor: '#e3f2fd',
    padding: '4px 8px',
    borderRadius: '4px',
  },
  expandIcon: {
    fontSize: '12px',
    color: '#888',
  },
  toolDescription: {
    fontSize: '14px',
    color: '#555',
    lineHeight: '1.5',
    margin: 0,
  },
  schemaSection: {
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid #eee',
  },
  schemaTitle: {
    fontSize: '13px',
    fontWeight: '600',
    color: '#666',
    marginBottom: '8px',
  },
  schemaCode: {
    fontSize: '12px',
    backgroundColor: '#f5f5f5',
    padding: '12px',
    borderRadius: '4px',
    overflow: 'auto',
    maxHeight: '300px',
  },
};
