import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { putServer } from '../shared/dynamodb';
import { created, badRequest, serverError } from '../shared/response';
import { McpServer, CreateServerRequest } from '../shared/types';
import { randomUUID } from 'crypto';

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Create server request');

  try {
    if (!event.body) {
      return badRequest('Request body is required');
    }

    const body: CreateServerRequest = JSON.parse(event.body);

    // Validate required fields
    if (!body.name?.trim()) {
      return badRequest('Server name is required');
    }

    if (!body.description?.trim()) {
      return badRequest('Server description is required');
    }

    if (!body.runtimeArn?.trim()) {
      return badRequest('Runtime ARN is required');
    }

    // Validate ARN format
    if (!body.runtimeArn.startsWith('arn:aws:bedrock-agentcore:')) {
      return badRequest('Invalid runtime ARN format. Expected arn:aws:bedrock-agentcore:...');
    }

    const now = new Date().toISOString();

    const server: McpServer = {
      serverId: randomUUID(),
      name: body.name.trim(),
      description: body.description.trim(),
      runtimeArn: body.runtimeArn.trim(),
      tags: body.tags || [],
      category: body.category || 'other',
      tools: [],
      status: 'active',
      createdAt: now,
      updatedAt: now,
    };

    await putServer(server);

    console.log('Created server:', server.serverId);

    return created(server);
  } catch (error) {
    if (error instanceof SyntaxError) {
      return badRequest('Invalid JSON in request body');
    }
    console.error('Create server error:', error);
    return serverError(String(error));
  }
}
