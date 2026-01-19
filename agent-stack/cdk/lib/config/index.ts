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
    rekognition: {
      name: 'rekognition_mcp',
      dockerPath: '../aws-mcp-server-agentcore/amazon-rekognition-mcp-server',
    },
    novaCanvas: {
      name: 'nova_canvas_mcp',
      dockerPath: '../aws-mcp-server-agentcore/nova-canvas-mcp-server',
    },
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
