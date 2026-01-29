import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { getServer, updateServerTools } from '../shared/dynamodb';
import { success, notFound, badRequest, serverError } from '../shared/response';
import { McpTool } from '../shared/types';
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

const REGION = process.env.AWS_REGION || 'us-west-2';
const MCP_CREDENTIALS_SECRET = process.env.MCP_CREDENTIALS_SECRET || 'acme-chatbot/mcp-credentials';

const secretsClient = new SecretsManagerClient({ region: REGION });

interface McpCredentials {
  MCP_COGNITO_CLIENT_ID: string;
  MCP_COGNITO_CLIENT_SECRET: string;
  MCP_COGNITO_DOMAIN: string;
  MCP_COGNITO_REGION: string;
  MCP_COGNITO_POOL_ID: string;
}

let cachedCredentials: McpCredentials | null = null;
let cachedToken: { token: string; expiry: number } | null = null;

async function getMcpCredentials(): Promise<McpCredentials> {
  if (cachedCredentials) {
    return cachedCredentials;
  }

  const command = new GetSecretValueCommand({ SecretId: MCP_CREDENTIALS_SECRET });
  const response = await secretsClient.send(command);

  if (!response.SecretString) {
    throw new Error('MCP credentials secret is empty');
  }

  cachedCredentials = JSON.parse(response.SecretString) as McpCredentials;
  return cachedCredentials;
}

async function getMcpToken(): Promise<string> {
  // Check if we have a valid cached token (with 5 min buffer)
  if (cachedToken && cachedToken.expiry > Date.now() + 5 * 60 * 1000) {
    return cachedToken.token;
  }

  const credentials = await getMcpCredentials();

  // Use OAuth2 client credentials flow
  const tokenUrl = `https://${credentials.MCP_COGNITO_DOMAIN}/oauth2/token`;

  const params = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: credentials.MCP_COGNITO_CLIENT_ID,
    client_secret: credentials.MCP_COGNITO_CLIENT_SECRET,
    scope: 'mcp/invoke',
  });

  console.log('Fetching MCP token from Cognito...');

  const response = await fetch(tokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params.toString(),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to get MCP token:', response.status, errorText);
    throw new Error(`Failed to get MCP token: ${response.status}`);
  }

  const data = await response.json();

  // Cache the token
  cachedToken = {
    token: data.access_token,
    expiry: Date.now() + (data.expires_in * 1000),
  };

  console.log('Got MCP token, expires in', data.expires_in, 'seconds');
  return cachedToken.token;
}

// Parse Server-Sent Events response to extract JSON data
function parseSSEResponse(sseText: string): Record<string, unknown> | null {
  const lines = sseText.split('\n');
  let dataBuffer = '';

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      dataBuffer += line.slice(6);
    } else if (line === '' && dataBuffer) {
      // End of event, try to parse
      try {
        return JSON.parse(dataBuffer);
      } catch {
        dataBuffer = '';
      }
    }
  }

  // Try to parse any remaining data
  if (dataBuffer) {
    try {
      return JSON.parse(dataBuffer);
    } catch {
      return null;
    }
  }

  return null;
}

async function fetchToolsFromMcpServer(runtimeArn: string): Promise<McpTool[]> {
  console.log('Fetching tools for runtime ARN:', runtimeArn);

  // Get MCP token using client credentials
  const authToken = await getMcpToken();

  // URL-encode the ARN for the endpoint
  const encodedArn = encodeURIComponent(runtimeArn);
  const endpoint = `https://bedrock-agentcore.${REGION}.amazonaws.com`;
  const path = `/runtimes/${encodedArn}/invocations`;
  const queryString = 'qualifier=DEFAULT';

  // MCP JSON-RPC request to initialize session
  const initRequest = {
    jsonrpc: '2.0',
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: {
        name: 'mcp-registry',
        version: '1.0.0',
      },
    },
    id: 1,
  };

  // Make initialize request with OAuth Bearer token
  console.log('Sending initialize request to MCP server...');
  let sessionId: string | undefined;

  try {
    const initResponse = await fetch(`${endpoint}${path}?${queryString}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': `Bearer ${authToken}`,
      },
      body: JSON.stringify(initRequest),
    });

    console.log('Initialize response status:', initResponse.status);

    if (!initResponse.ok) {
      const errorText = await initResponse.text();
      console.warn('Initialize failed:', initResponse.status, errorText);
      return [];
    }

    // Get session ID from response headers
    sessionId = initResponse.headers.get('mcp-session-id') || undefined;
    console.log('Session ID:', sessionId);

    // Read response - might be JSON or SSE
    const responseText = await initResponse.text();
    const contentType = initResponse.headers.get('content-type') || '';

    let initData: Record<string, unknown> | null = null;

    if (contentType.includes('text/event-stream')) {
      console.log('Parsing SSE response...');
      initData = parseSSEResponse(responseText);
    } else {
      initData = JSON.parse(responseText);
    }

    console.log('Initialize response:', JSON.stringify(initData));
  } catch (error) {
    console.error('Initialize request failed:', error);
    return [];
  }

  // Now request tools/list
  const listToolsRequest = {
    jsonrpc: '2.0',
    method: 'tools/list',
    params: {},
    id: 2,
  };

  console.log('Sending tools/list request...');

  try {
    const listResponse = await fetch(`${endpoint}${path}?${queryString}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': `Bearer ${authToken}`,
        ...(sessionId ? { 'Mcp-Session-Id': sessionId } : {}),
      },
      body: JSON.stringify(listToolsRequest),
    });

    console.log('Tools list response status:', listResponse.status);

    if (!listResponse.ok) {
      const errorText = await listResponse.text();
      console.warn('Tools list failed:', listResponse.status, errorText);
      return [];
    }

    // Read response - might be JSON or SSE
    const responseText = await listResponse.text();
    const contentType = listResponse.headers.get('content-type') || '';

    let listData: Record<string, unknown> | null = null;

    if (contentType.includes('text/event-stream')) {
      console.log('Parsing SSE response for tools/list...');
      listData = parseSSEResponse(responseText);
    } else {
      listData = JSON.parse(responseText);
    }

    console.log('Tools list response:', JSON.stringify(listData));

    if (!listData) {
      console.log('Failed to parse tools list response');
      return [];
    }

    // Parse MCP tools response
    // MCP response format: { jsonrpc: "2.0", result: { tools: [...] }, id: 2 }
    const result = listData.result as Record<string, unknown> | undefined;
    if (result && result.tools && Array.isArray(result.tools)) {
      return result.tools.map((tool: Record<string, unknown>) => ({
        name: (tool.name as string) || 'unknown',
        description: (tool.description as string) || '',
        inputSchema: tool.inputSchema as Record<string, unknown>,
      }));
    }

    // Alternative response format
    if (listData.tools && Array.isArray(listData.tools)) {
      return (listData.tools as Record<string, unknown>[]).map((tool) => ({
        name: (tool.name as string) || 'unknown',
        description: (tool.description as string) || '',
        inputSchema: tool.inputSchema as Record<string, unknown>,
      }));
    }

    console.log('No tools found in response');
    return [];
  } catch (error) {
    console.error('Tools list request failed:', error);
    return [];
  }
}

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Get tools request:', event.pathParameters);

  try {
    const serverId = event.pathParameters?.id;
    const forceRefresh = event.queryStringParameters?.refresh === 'true';

    if (!serverId) {
      return badRequest('Server ID is required');
    }

    const server = await getServer(serverId);

    if (!server) {
      return notFound(`Server with ID ${serverId} not found`);
    }

    // Return cached tools if available and not forcing refresh
    if (!forceRefresh && server.tools && server.tools.length > 0) {
      return success({
        serverId: server.serverId,
        serverName: server.name,
        tools: server.tools,
        toolsUpdatedAt: server.toolsUpdatedAt,
        cached: true,
      });
    }

    // Fetch tools from MCP server using service credentials
    let tools: McpTool[] = [];

    try {
      tools = await fetchToolsFromMcpServer(server.runtimeArn);
      console.log(`Fetched ${tools.length} tools from MCP server`);
    } catch (mcpError) {
      console.warn('Failed to fetch tools from MCP server:', mcpError);
    }

    // Update cached tools in DynamoDB
    await updateServerTools(serverId, tools);

    return success({
      serverId: server.serverId,
      serverName: server.name,
      tools,
      toolsUpdatedAt: new Date().toISOString(),
      cached: false,
    });
  } catch (error) {
    console.error('Get tools error:', error);
    return serverError(String(error));
  }
}
