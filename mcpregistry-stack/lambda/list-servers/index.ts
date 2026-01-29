import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { listServers } from '../shared/dynamodb';
import { success, serverError } from '../shared/response';
import { ListServersQuery } from '../shared/types';

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('List servers request:', JSON.stringify(event.queryStringParameters));

  try {
    const params = event.queryStringParameters || {};

    const query: ListServersQuery = {
      category: params.category,
      status: params.status,
      search: params.search,
      limit: params.limit ? parseInt(params.limit, 10) : undefined,
      lastKey: params.lastKey,
    };

    const result = await listServers(query);

    return success(result);
  } catch (error) {
    console.error('List servers error:', error);
    return serverError(String(error));
  }
}
