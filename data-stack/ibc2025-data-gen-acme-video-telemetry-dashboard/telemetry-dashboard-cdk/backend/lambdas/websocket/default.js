exports.handler = async (event) => {
  console.log('Default route event:', JSON.stringify(event));
  
  const connectionId = event.requestContext.connectionId;
  const body = JSON.parse(event.body || '{}');
  
  console.log(`Message from ${connectionId}:`, body);
  
  // Handle different message types
  switch (body.action) {
    case 'ping':
      return {
        statusCode: 200,
        body: JSON.stringify({ action: 'pong', timestamp: new Date().toISOString() })
      };
      
    case 'subscribe':
      console.log(`Connection ${connectionId} subscribing to events`);
      return {
        statusCode: 200,
        body: JSON.stringify({ action: 'subscribed', message: 'Subscribed to telemetry events' })
      };
      
    default:
      return {
        statusCode: 200,
        body: JSON.stringify({ action: 'ack', message: 'Message received' })
      };
  }
};