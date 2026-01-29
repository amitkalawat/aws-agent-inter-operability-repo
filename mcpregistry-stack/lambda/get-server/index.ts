import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { getServer } from '../shared/dynamodb';
import { success, notFound, badRequest, serverError } from '../shared/response';

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Get server request:', event.pathParameters);

  try {
    const serverId = event.pathParameters?.id;

    if (!serverId) {
      return badRequest('Server ID is required');
    }

    const server = await getServer(serverId);

    if (!server) {
      return notFound(`Server with ID ${serverId} not found`);
    }

    return success(server);
  } catch (error) {
    console.error('Get server error:', error);
    return serverError(String(error));
  }
}
