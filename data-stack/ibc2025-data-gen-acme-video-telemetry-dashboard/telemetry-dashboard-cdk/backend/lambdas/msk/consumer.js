const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, ScanCommand, DeleteCommand } = require('@aws-sdk/lib-dynamodb');
const { ApiGatewayManagementApiClient, PostToConnectionCommand } = require('@aws-sdk/client-apigatewaymanagementapi');

const client = new DynamoDBClient({});
const dynamodb = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
  console.log('MSK Event received:', JSON.stringify(event));
  
  // Validate required environment variables
  if (!process.env.WEBSOCKET_ENDPOINT) {
    console.error('WEBSOCKET_ENDPOINT environment variable is not set');
    throw new Error('Missing WEBSOCKET_ENDPOINT configuration');
  }
  
  if (!process.env.CONNECTIONS_TABLE) {
    console.error('CONNECTIONS_TABLE environment variable is not set');
    throw new Error('Missing CONNECTIONS_TABLE configuration');
  }
  
  console.log('WebSocket Endpoint:', process.env.WEBSOCKET_ENDPOINT);
  console.log('Connections Table:', process.env.CONNECTIONS_TABLE);
  
  const apigateway = new ApiGatewayManagementApiClient({
    endpoint: process.env.WEBSOCKET_ENDPOINT
  });
  
  try {
    // Parse Kafka records from Lambda event source mapping
    const telemetryEvents = [];
    
    // Process each Kafka record
    for (const topicPartition in event.records) {
      const messages = event.records[topicPartition];
      
      for (const message of messages) {
        // Decode the Kafka message
        const decodedValue = Buffer.from(message.value, 'base64').toString('utf-8');
        let telemetryEvent;
        
        try {
          telemetryEvent = JSON.parse(decodedValue);
        } catch (parseError) {
          console.error('Error parsing message:', parseError);
          continue;
        }
        
        // Add metadata
        telemetryEvent.receivedAt = new Date().toISOString();
        telemetryEvent.partition = topicPartition;
        telemetryEvent.offset = message.offset;
        telemetryEvent.timestamp = new Date(message.timestamp).toISOString();
        
        telemetryEvents.push(telemetryEvent);
      }
    }
    
    console.log(`Processing ${telemetryEvents.length} telemetry events`);
    
    // Get all active WebSocket connections from DynamoDB
    const connections = await getActiveConnections();
    console.log(`Found ${connections.length} active connections`);
    
    // Broadcast to all connected clients
    await broadcastToClients(apigateway, connections, telemetryEvents);
    
    console.log(`Successfully processed ${telemetryEvents.length} events and notified ${connections.length} connections`);
    
    return { 
      batchItemFailures: [],
      statusCode: 200,
      message: `Processed ${telemetryEvents.length} events`
    };
  } catch (error) {
    console.error('Error processing MSK events:', error);
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      name: error.name
    });
    
    // For critical configuration errors, fail the batch
    if (error.message && error.message.includes('Missing')) {
      throw error;
    }
    
    // For other errors, acknowledge the batch to prevent reprocessing
    // but log the error for debugging
    return { batchItemFailures: [] };
  }
};

async function getActiveConnections() {
  try {
    console.log(`Scanning connections table: ${process.env.CONNECTIONS_TABLE}`);
    
    const result = await dynamodb.send(new ScanCommand({
      TableName: process.env.CONNECTIONS_TABLE,
      ProjectionExpression: 'connectionId, userId'
    }));
    
    const connections = result.Items || [];
    console.log(`Found ${connections.length} active connections in DynamoDB`);
    
    if (connections.length > 0) {
      console.log('Active connections:', connections.map(c => ({
        connectionId: c.connectionId,
        userId: c.userId
      })));
    }
    
    return connections;
  } catch (error) {
    console.error('Error scanning connections:', error);
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      statusCode: error.statusCode
    });
    return [];
  }
}

async function broadcastToClients(apigateway, connections, events) {
  if (connections.length === 0) {
    console.log('No active connections to broadcast to');
    return;
  }
  
  console.log(`Broadcasting ${events.length} events to ${connections.length} connections`);
  
  const postCalls = connections.map(async ({ connectionId, userId }) => {
    try {
      const payload = JSON.stringify({
        action: 'telemetry',
        events: events,
        timestamp: new Date().toISOString()
      });
      
      console.log(`Sending to connection ${connectionId} (user: ${userId}), payload size: ${payload.length} bytes`);
      
      // Send events to each connection
      await apigateway.send(new PostToConnectionCommand({
        ConnectionId: connectionId,
        Data: payload
      }));
      
      console.log(`Successfully sent ${events.length} events to connection ${connectionId} (user: ${userId})`);
    } catch (error) {
      console.error(`Error sending to connection ${connectionId}:`, error);
      console.error('Error details:', {
        statusCode: error.statusCode,
        message: error.message,
        code: error.code,
        name: error.name
      });
      
      if (error.statusCode === 410 || error.name === 'GoneException') {
        // Connection is stale, remove it
        console.log(`Removing stale connection: ${connectionId}`);
        try {
          await dynamodb.send(new DeleteCommand({
            TableName: process.env.CONNECTIONS_TABLE,
            Key: { connectionId }
          }));
          console.log(`Successfully removed stale connection: ${connectionId}`);
        } catch (deleteError) {
          console.error(`Error removing stale connection ${connectionId}:`, deleteError);
        }
      }
    }
  });
  
  await Promise.all(postCalls);
  console.log('Completed broadcasting to all connections');
}