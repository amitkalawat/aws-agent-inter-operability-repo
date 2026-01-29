export interface McpServer {
  serverId: string;
  name: string;
  description: string;
  runtimeArn: string;
  tags: string[];
  category: 'documentation' | 'data' | 'vision' | 'generation' | 'other';
  tools: McpTool[];
  toolsUpdatedAt?: string;
  status: 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
}

export interface McpTool {
  name: string;
  description: string;
  inputSchema?: Record<string, unknown>;
}

export interface ToolsResponse {
  serverId: string;
  serverName: string;
  tools: McpTool[];
  toolsUpdatedAt: string;
  cached: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  lastKey?: string;
  count: number;
}
