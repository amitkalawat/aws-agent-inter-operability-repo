import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { RegistryService } from '../services/RegistryService';
import { McpServer } from '../types';

const categories: Array<{ value: McpServer['category']; label: string }> = [
  { value: 'documentation', label: 'Documentation' },
  { value: 'data', label: 'Data & Analytics' },
  { value: 'vision', label: 'Vision & Image' },
  { value: 'generation', label: 'Generation' },
  { value: 'other', label: 'Other' },
];

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [runtimeArn, setRuntimeArn] = useState('');
  const [category, setCategory] = useState<McpServer['category']>('other');
  const [tagsInput, setTagsInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!name.trim()) {
      setError('Server name is required');
      return;
    }
    if (!description.trim()) {
      setError('Description is required');
      return;
    }
    if (!runtimeArn.trim()) {
      setError('Runtime ARN is required');
      return;
    }
    if (!runtimeArn.startsWith('arn:aws:bedrock-agentcore:')) {
      setError('Invalid Runtime ARN format. Expected arn:aws:bedrock-agentcore:...');
      return;
    }

    setSubmitting(true);

    try {
      const tags = tagsInput
        .split(',')
        .map((t) => t.trim().toLowerCase())
        .filter((t) => t.length > 0);

      const server = await RegistryService.createServer({
        name: name.trim(),
        description: description.trim(),
        runtimeArn: runtimeArn.trim(),
        category,
        tags,
      });

      navigate(`/servers/${server.serverId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to register server');
      setSubmitting(false);
    }
  };

  return (
    <div style={styles.container}>
      <Link to="/" style={styles.backLink}>
        &larr; Back to Registry
      </Link>

      <div style={styles.card}>
        <h1 style={styles.title}>Register MCP Server</h1>
        <p style={styles.subtitle}>
          Add a new MCP server to the registry. The server must be deployed on
          AWS Bedrock AgentCore.
        </p>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Server Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., My Documentation Server"
              style={styles.input}
              disabled={submitting}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Description *</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this MCP server does..."
              style={styles.textarea}
              rows={3}
              disabled={submitting}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Runtime ARN *</label>
            <input
              type="text"
              value={runtimeArn}
              onChange={(e) => setRuntimeArn(e.target.value)}
              placeholder="arn:aws:bedrock-agentcore:us-west-2:123456789:runtime/my-server"
              style={styles.input}
              disabled={submitting}
            />
            <span style={styles.hint}>
              The ARN of your AgentCore runtime hosting the MCP server
            </span>
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as McpServer['category'])}
              style={styles.select}
              disabled={submitting}
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Tags</label>
            <input
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="e.g., aws, documentation, search"
              style={styles.input}
              disabled={submitting}
            />
            <span style={styles.hint}>
              Comma-separated list of tags for search and filtering
            </span>
          </div>

          <div style={styles.actions}>
            <Link to="/" style={styles.cancelBtn}>
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              style={styles.submitBtn}
            >
              {submitting ? 'Registering...' : 'Register Server'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '24px',
  },
  backLink: {
    color: '#666',
    textDecoration: 'none',
    fontSize: '14px',
    display: 'inline-block',
    marginBottom: '20px',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '32px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  title: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#232f3e',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '24px',
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '12px 16px',
    borderRadius: '4px',
    fontSize: '14px',
    marginBottom: '20px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  input: {
    padding: '10px 14px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    outline: 'none',
  },
  textarea: {
    padding: '10px 14px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    outline: 'none',
    resize: 'vertical',
    fontFamily: 'inherit',
  },
  select: {
    padding: '10px 14px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    outline: 'none',
    backgroundColor: 'white',
  },
  hint: {
    fontSize: '12px',
    color: '#888',
  },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
    marginTop: '12px',
  },
  cancelBtn: {
    padding: '10px 20px',
    fontSize: '14px',
    color: '#666',
    textDecoration: 'none',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: 'white',
  },
  submitBtn: {
    padding: '10px 24px',
    fontSize: '14px',
    backgroundColor: '#ff9900',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
  },
};
