const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, DeleteCommand } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({});
const dynamodb = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
  console.log('Disconnect event:', JSON.stringify(event));
  
  const connectionId = event.requestContext.connectionId;
  
  try {
    // Remove connection from DynamoDB
    await dynamodb.send(new DeleteCommand({
      TableName: process.env.CONNECTIONS_TABLE,
      Key: { connectionId }
    }));
    
    console.log(`Connection ${connectionId} removed`);
    
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Disconnected successfully' })
    };
  } catch (error) {
    console.error('Error removing connection:', error);
    // Don't fail on disconnect errors
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Disconnected' })
    };
  }
};