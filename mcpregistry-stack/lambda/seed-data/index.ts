import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';
import { CloudFormationCustomResourceEvent, CloudFormationCustomResourceResponse } from 'aws-lambda';
import { randomUUID } from 'crypto';

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

const TABLE_NAME = process.env.TABLE_NAME!;

interface SeedServer {
  name: string;
  description: string;
  category: string;
  tags: string[];
  arnEnvVar: string;
}

const seedServers: SeedServer[] = [
  {
    name: 'AWS Documentation',
    description: 'Search and retrieve AWS documentation, best practices, and service guides',
    category: 'documentation',
    tags: ['aws', 'docs', 'documentation', 'search'],
    arnEnvVar: 'AWS_DOCS_MCP_ARN',
  },
  {
    name: 'Data Processing',
    description: 'Query ACME telemetry data using Athena SQL. Analyze streaming events, customer data, and campaigns.',
    category: 'data',
    tags: ['athena', 'sql', 'analytics', 'telemetry', 'data'],
    arnEnvVar: 'DATAPROC_MCP_ARN',
  },
  {
    name: 'Amazon Rekognition',
    description: 'Analyze images for labels, text, faces, celebrities, and content moderation using Amazon Rekognition.',
    category: 'vision',
    tags: ['rekognition', 'image', 'vision', 'analysis', 'ai'],
    arnEnvVar: 'REKOGNITION_MCP_ARN',
  },
  {
    name: 'Nova Canvas',
    description: 'Generate AI images using Amazon Nova Canvas. Create images from text prompts with various styles.',
    category: 'generation',
    tags: ['nova', 'canvas', 'image', 'generation', 'ai', 'creative'],
    arnEnvVar: 'NOVA_CANVAS_MCP_ARN',
  },
];

export async function handler(
  event: CloudFormationCustomResourceEvent
): Promise<CloudFormationCustomResourceResponse> {
  console.log('Seed data event:', JSON.stringify(event, null, 2));

  const requestType = event.RequestType;

  if (requestType === 'Delete') {
    // Don't delete data on stack deletion for safety
    return {
      Status: 'SUCCESS',
      PhysicalResourceId: event.PhysicalResourceId || 'seed-data',
      StackId: event.StackId,
      RequestId: event.RequestId,
      LogicalResourceId: event.LogicalResourceId,
    };
  }

  try {
    // Check if data already exists
    const existingData = await docClient.send(
      new ScanCommand({
        TableName: TABLE_NAME,
        Limit: 1,
      })
    );

    if (existingData.Items && existingData.Items.length > 0 && requestType === 'Update') {
      console.log('Data already exists, skipping seed');
      return {
        Status: 'SUCCESS',
        PhysicalResourceId: event.PhysicalResourceId || 'seed-data',
        StackId: event.StackId,
        RequestId: event.RequestId,
        LogicalResourceId: event.LogicalResourceId,
      };
    }

    const now = new Date().toISOString();

    for (const server of seedServers) {
      const runtimeArn = process.env[server.arnEnvVar];

      if (!runtimeArn) {
        console.warn(`Missing ARN for ${server.name} (${server.arnEnvVar})`);
        continue;
      }

      const item = {
        serverId: randomUUID(),
        name: server.name,
        description: server.description,
        runtimeArn,
        tags: server.tags,
        category: server.category,
        tools: [],
        status: 'active',
        createdAt: now,
        updatedAt: now,
      };

      await docClient.send(
        new PutCommand({
          TableName: TABLE_NAME,
          Item: item,
          ConditionExpression: 'attribute_not_exists(serverId)',
        })
      );

      console.log(`Seeded server: ${server.name}`);
    }

    return {
      Status: 'SUCCESS',
      PhysicalResourceId: 'seed-data',
      StackId: event.StackId,
      RequestId: event.RequestId,
      LogicalResourceId: event.LogicalResourceId,
    };
  } catch (error) {
    console.error('Seed error:', error);
    return {
      Status: 'FAILED',
      Reason: String(error),
      PhysicalResourceId: event.PhysicalResourceId || 'seed-data',
      StackId: event.StackId,
      RequestId: event.RequestId,
      LogicalResourceId: event.LogicalResourceId,
    };
  }
}
