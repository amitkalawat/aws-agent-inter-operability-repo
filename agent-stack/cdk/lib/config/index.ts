/**
 * Configuration constants for ACME AgentCore Stack
 */

export const Config = {
  // AWS Configuration
  aws: {
    region: 'us-west-2',
    platform: 'linux/arm64',
  },

  // Project naming
  naming: {
    projectPrefix: 'acme',
    stackName: 'AcmeAgentCoreStack',
  },

  // Cognito Configuration
  cognito: {
    userPoolName: 'acme-corp-agentcore-users',
    frontendClientName: 'acme-frontend-client',
    mcpClientName: 'acme-mcp-client',
    passwordPolicy: {
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireDigits: true,
      requireSymbols: true,
      tempPasswordValidityDays: 7,
    },
    tokenValidity: {
      idToken: 24, // hours
      accessToken: 24, // hours
      refreshToken: 30, // days
    },
  },

  // Agent Configuration
  agent: {
    runtimeName: 'acme_chatbot',
    model: 'global.anthropic.claude-haiku-4-5-20251001-v1:0',
    memory: {
      name: 'acme_chat_memory',
      expirationDays: 90,
    },
  },

  // MCP Servers Configuration
  // Docker paths are relative to the cdk/lib directory
  mcpServers: {
    awsDocs: {
      name: 'aws_docs_mcp',
      dockerPath: '../aws-mcp-server-agentcore/aws-documentation-mcp-server',
    },
    dataProcessing: {
      name: 'dataproc_mcp',
      dockerPath: '../aws-mcp-server-agentcore/aws-dataprocessing-mcp-server',
    },
  },

  // MCP Gateway Configuration
  // Aggregates all MCP servers behind a single endpoint
  gateway: {
    name: 'acme-mcp-gateway',
    description: 'ACME Corp unified MCP Gateway for tool aggregation',
    searchType: 'SEMANTIC' as const, // 'SEMANTIC' for AI-powered tool discovery, 'NONE' for exact match
    mcpVersions: ['2025-03-26'],
  },

  // Visualization bucket for code interpreter charts
  visualization: {
    bucketPrefix: 'acme-visualizations',
    expirationDays: 1,
  },

  // Frontend Configuration
  frontend: {
    bucketNamePrefix: 'acme-chat-frontend',
    buildPath: '../frontend/acme-chat/build',
    cachePolicy: {
      staticAssetsTtlDays: 30,
      staticAssetsMaxTtlDays: 365,
    },
  },

  // Secrets Manager Configuration
  secrets: {
    mcpCredentialsName: 'acme-chatbot/mcp-credentials',
  },

  // Tags
  tags: {
    Project: 'ACME-Corp-AgentCore',
    Environment: 'Production',
    ManagedBy: 'CDK',
  },
} as const;

export type ConfigType = typeof Config;
