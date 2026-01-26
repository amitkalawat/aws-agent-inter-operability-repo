const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { ScanCommand, DeleteCommand, DynamoDBDocumentClient } = require('@aws-sdk/lib-dynamodb');
const { ApiGatewayManagementApiClient, PostToConnectionCommand } = require('@aws-sdk/client-apigatewaymanagementapi');

const ddbClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(ddbClient);

exports.handler = async (event) => {
  const tableName = process.env.CONNECTIONS_TABLE;
  const wsEndpoint = process.env.WEBSOCKET_ENDPOINT;

  if (!wsEndpoint) {
    console.error('WEBSOCKET_ENDPOINT not set');
    return { statusCode: 500 };
  }

  const apiClient = new ApiGatewayManagementApiClient({
    endpoint: wsEndpoint,
  });

  // Parse MSK records
  const messages = [];
  for (const [topic, partitions] of Object.entries(event.records || {})) {
    for (const record of partitions) {
      try {
        const value = Buffer.from(record.value, 'base64').toString('utf-8');
        messages.push(JSON.parse(value));
      } catch (e) {
        console.error('Failed to parse record:', e);
      }
    }
  }

  if (messages.length === 0) {
    return { statusCode: 200, body: 'No messages' };
  }

  // Get all connections
  let connections = [];
  try {
    const result = await docClient.send(new ScanCommand({ TableName: tableName }));
    connections = result.Items || [];
  } catch (error) {
    console.error('Failed to scan connections:', error);
    return { statusCode: 500 };
  }

  // Broadcast to all connections
  const payload = JSON.stringify({ type: 'telemetry', data: messages });

  await Promise.all(connections.map(async ({ connectionId }) => {
    try {
      await apiClient.send(new PostToConnectionCommand({
        ConnectionId: connectionId,
        Data: payload,
      }));
    } catch (error) {
      if (error.statusCode === 410) {
        // Connection stale, remove from DynamoDB
        await docClient.send(new DeleteCommand({
          TableName: tableName,
          Key: { connectionId },
        }));
      } else {
        console.error(`Failed to send to ${connectionId}:`, error);
      }
    }
  }));

  return { statusCode: 200, body: `Broadcast ${messages.length} events to ${connections.length} connections` };
};
