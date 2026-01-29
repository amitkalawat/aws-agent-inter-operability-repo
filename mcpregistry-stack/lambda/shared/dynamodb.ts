import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import {
  DynamoDBDocumentClient,
  GetCommand,
  PutCommand,
  DeleteCommand,
  ScanCommand,
  QueryCommand,
  UpdateCommand,
} from '@aws-sdk/lib-dynamodb';
import { McpServer, ListServersQuery, PaginatedResponse } from './types';

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client, {
  marshallOptions: { removeUndefinedValues: true },
});

const TABLE_NAME = process.env.TABLE_NAME!;
const CATEGORY_INDEX = process.env.CATEGORY_INDEX || 'category-index';
const STATUS_INDEX = process.env.STATUS_INDEX || 'status-index';

export async function getServer(serverId: string): Promise<McpServer | null> {
  const result = await docClient.send(
    new GetCommand({
      TableName: TABLE_NAME,
      Key: { serverId },
    })
  );
  return (result.Item as McpServer) || null;
}

export async function putServer(server: McpServer): Promise<void> {
  await docClient.send(
    new PutCommand({
      TableName: TABLE_NAME,
      Item: server,
    })
  );
}

export async function deleteServer(serverId: string): Promise<void> {
  await docClient.send(
    new DeleteCommand({
      TableName: TABLE_NAME,
      Key: { serverId },
    })
  );
}

export async function listServers(
  query: ListServersQuery
): Promise<PaginatedResponse<McpServer>> {
  const limit = query.limit || 50;
  let exclusiveStartKey: Record<string, unknown> | undefined;

  if (query.lastKey) {
    try {
      exclusiveStartKey = JSON.parse(Buffer.from(query.lastKey, 'base64').toString());
    } catch {
      exclusiveStartKey = undefined;
    }
  }

  let result;

  if (query.category) {
    // Query by category using GSI
    result = await docClient.send(
      new QueryCommand({
        TableName: TABLE_NAME,
        IndexName: CATEGORY_INDEX,
        KeyConditionExpression: 'category = :category',
        ExpressionAttributeValues: {
          ':category': query.category,
        },
        Limit: limit,
        ExclusiveStartKey: exclusiveStartKey,
        ScanIndexForward: false, // newest first
      })
    );
  } else if (query.status) {
    // Query by status using GSI
    result = await docClient.send(
      new QueryCommand({
        TableName: TABLE_NAME,
        IndexName: STATUS_INDEX,
        KeyConditionExpression: '#status = :status',
        ExpressionAttributeNames: {
          '#status': 'status',
        },
        ExpressionAttributeValues: {
          ':status': query.status,
        },
        Limit: limit,
        ExclusiveStartKey: exclusiveStartKey,
      })
    );
  } else {
    // Full table scan
    result = await docClient.send(
      new ScanCommand({
        TableName: TABLE_NAME,
        Limit: limit,
        ExclusiveStartKey: exclusiveStartKey,
      })
    );
  }

  let items = (result.Items as McpServer[]) || [];

  // Client-side search filtering if search query provided
  if (query.search) {
    const searchLower = query.search.toLowerCase();
    items = items.filter(
      (server) =>
        server.name.toLowerCase().includes(searchLower) ||
        server.description.toLowerCase().includes(searchLower) ||
        server.tags.some((tag) => tag.toLowerCase().includes(searchLower))
    );
  }

  let lastKey: string | undefined;
  if (result.LastEvaluatedKey) {
    lastKey = Buffer.from(JSON.stringify(result.LastEvaluatedKey)).toString('base64');
  }

  return {
    items,
    lastKey,
    count: items.length,
  };
}

export async function updateServerTools(
  serverId: string,
  tools: McpServer['tools']
): Promise<void> {
  await docClient.send(
    new UpdateCommand({
      TableName: TABLE_NAME,
      Key: { serverId },
      UpdateExpression: 'SET tools = :tools, toolsUpdatedAt = :updatedAt, updatedAt = :updatedAt',
      ExpressionAttributeValues: {
        ':tools': tools,
        ':updatedAt': new Date().toISOString(),
      },
    })
  );
}
