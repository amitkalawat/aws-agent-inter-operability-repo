import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { getServer, deleteServer } from '../shared/dynamodb';
import { noContent, notFound, badRequest, serverError } from '../shared/response';

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Delete server request:', event.pathParameters);

  try {
    const serverId = event.pathParameters?.id;

    if (!serverId) {
      return badRequest('Server ID is required');
    }

    // Check if server exists
    const existing = await getServer(serverId);

    if (!existing) {
      return notFound(`Server with ID ${serverId} not found`);
    }

    await deleteServer(serverId);

    console.log('Deleted server:', serverId);

    return noContent();
  } catch (error) {
    console.error('Delete server error:', error);
    return serverError(String(error));
  }
}
