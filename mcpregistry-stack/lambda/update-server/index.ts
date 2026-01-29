import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { getServer, putServer } from '../shared/dynamodb';
import { success, notFound, badRequest, serverError } from '../shared/response';
import { UpdateServerRequest } from '../shared/types';

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Update server request:', event.pathParameters);

  try {
    const serverId = event.pathParameters?.id;

    if (!serverId) {
      return badRequest('Server ID is required');
    }

    if (!event.body) {
      return badRequest('Request body is required');
    }

    const body: UpdateServerRequest = JSON.parse(event.body);

    // Get existing server
    const existing = await getServer(serverId);

    if (!existing) {
      return notFound(`Server with ID ${serverId} not found`);
    }

    // Validate ARN format if provided
    if (body.runtimeArn && !body.runtimeArn.startsWith('arn:aws:bedrock-agentcore:')) {
      return badRequest('Invalid runtime ARN format. Expected arn:aws:bedrock-agentcore:...');
    }

    // Update fields
    const updated = {
      ...existing,
      name: body.name?.trim() || existing.name,
      description: body.description?.trim() || existing.description,
      runtimeArn: body.runtimeArn?.trim() || existing.runtimeArn,
      tags: body.tags !== undefined ? body.tags : existing.tags,
      category: body.category || existing.category,
      status: body.status || existing.status,
      updatedAt: new Date().toISOString(),
    };

    await putServer(updated);

    console.log('Updated server:', serverId);

    return success(updated);
  } catch (error) {
    if (error instanceof SyntaxError) {
      return badRequest('Invalid JSON in request body');
    }
    console.error('Update server error:', error);
    return serverError(String(error));
  }
}
