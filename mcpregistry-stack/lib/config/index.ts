export const Config = {
  aws: {
    region: 'us-west-2',
  },

  naming: {
    prefix: 'mcp-registry',
  },

  dynamodb: {
    tableName: 'mcp-registry-servers',
    categoryIndex: 'category-index',
    statusIndex: 'status-index',
  },

  api: {
    stageName: 'prod',
  },

  // CloudFormation exports from agent-stack to import
  imports: {
    userPoolId: 'AcmeUserPoolId',
    frontendClientId: 'AcmeFrontendClientId',
    discoveryUrl: 'AcmeDiscoveryUrl',
    awsDocsMcpArn: 'AcmeAwsDocsMcpArn',
    dataprocMcpArn: 'AcmeDataprocMcpArn',
    rekognitionMcpArn: 'AcmeRekognitionMcpArn',
    novaCanvasMcpArn: 'AcmeNovaCanvasMcpArn',
  },

  // Seed data for MCP servers (populated on deploy)
  seedServers: [
    {
      name: 'AWS Documentation',
      description: 'Search and retrieve AWS documentation, best practices, and service guides',
      category: 'documentation',
      tags: ['aws', 'docs', 'documentation', 'search'],
      arnExportKey: 'awsDocsMcpArn',
    },
    {
      name: 'Data Processing',
      description: 'Query ACME telemetry data using Athena SQL. Analyze streaming events, customer data, and campaigns.',
      category: 'data',
      tags: ['athena', 'sql', 'analytics', 'telemetry', 'data'],
      arnExportKey: 'dataprocMcpArn',
    },
    {
      name: 'Amazon Rekognition',
      description: 'Analyze images for labels, text, faces, celebrities, and content moderation using Amazon Rekognition.',
      category: 'vision',
      tags: ['rekognition', 'image', 'vision', 'analysis', 'ai'],
      arnExportKey: 'rekognitionMcpArn',
    },
    {
      name: 'Nova Canvas',
      description: 'Generate AI images using Amazon Nova Canvas. Create images from text prompts with various styles.',
      category: 'generation',
      tags: ['nova', 'canvas', 'image', 'generation', 'ai', 'creative'],
      arnExportKey: 'novaCanvasMcpArn',
    },
  ],
};
