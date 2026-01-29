import { APIGatewayProxyResult } from 'aws-lambda';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
  'Content-Type': 'application/json',
};

export function success(body: unknown): APIGatewayProxyResult {
  return {
    statusCode: 200,
    headers: corsHeaders,
    body: JSON.stringify(body),
  };
}

export function created(body: unknown): APIGatewayProxyResult {
  return {
    statusCode: 201,
    headers: corsHeaders,
    body: JSON.stringify(body),
  };
}

export function noContent(): APIGatewayProxyResult {
  return {
    statusCode: 204,
    headers: corsHeaders,
    body: '',
  };
}

export function badRequest(message: string): APIGatewayProxyResult {
  return {
    statusCode: 400,
    headers: corsHeaders,
    body: JSON.stringify({ error: 'Bad Request', message }),
  };
}

export function notFound(message: string = 'Resource not found'): APIGatewayProxyResult {
  return {
    statusCode: 404,
    headers: corsHeaders,
    body: JSON.stringify({ error: 'Not Found', message }),
  };
}

export function serverError(message: string = 'Internal server error'): APIGatewayProxyResult {
  console.error('Server error:', message);
  return {
    statusCode: 500,
    headers: corsHeaders,
    body: JSON.stringify({ error: 'Internal Server Error', message }),
  };
}
