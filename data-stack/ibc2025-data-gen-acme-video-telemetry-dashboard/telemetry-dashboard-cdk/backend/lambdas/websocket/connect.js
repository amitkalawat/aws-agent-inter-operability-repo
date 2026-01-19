const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({});
const dynamodb = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
  console.log('Connect event:', JSON.stringify(event));
  
  const connectionId = event.requestContext.connectionId;
  const timestamp = new Date().toISOString();
  
  // Extract user info from JWT token since WebSocket authorizer context isn't passed through
  let userId = 'anonymous';
  const token = event.queryStringParameters?.token;
  if (token) {
    try {
      // Decode JWT token (no verification needed since authorizer already validated it)
      const sections = token.split('.');
      if (sections.length === 3) {
        const payload = JSON.parse(Buffer.from(sections[1], 'base64').toString('utf8'));
        userId = payload['cognito:username'] || payload.email || 'anonymous';
        console.log(`Extracted userId: ${userId} from token`);
      }
    } catch (error) {
      console.error('Error extracting user from token:', error);
    }
  }
  
  try {
    // Store connection in DynamoDB
    await dynamodb.send(new PutCommand({
      TableName: process.env.CONNECTIONS_TABLE,
      Item: {
        connectionId,
        userId,
        connectedAt: timestamp,
        ttl: Math.floor(Date.now() / 1000) + 7200 // 2 hours TTL
      }
    }));
    
    console.log(`Connection ${connectionId} stored for user ${userId}`);
    
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Connected successfully' })
    };
  } catch (error) {
    console.error('Error storing connection:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to connect' })
    };
  }
};