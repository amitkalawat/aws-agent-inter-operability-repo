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

export interface CreateServerRequest {
  name: string;
  description: string;
  runtimeArn: string;
  tags?: string[];
  category?: McpServer['category'];
}

export interface UpdateServerRequest {
  name?: string;
  description?: string;
  runtimeArn?: string;
  tags?: string[];
  category?: McpServer['category'];
  status?: McpServer['status'];
}

export interface ListServersQuery {
  category?: string;
  status?: string;
  search?: string;
  limit?: number;
  lastKey?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  lastKey?: string;
  count: number;
}
