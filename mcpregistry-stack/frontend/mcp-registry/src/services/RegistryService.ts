import { config } from '../config';
import { AuthService } from './AuthService';
import { McpServer, ToolsResponse, PaginatedResponse } from '../types';

class RegistryServiceClass {
  private baseUrl = config.api.baseUrl;

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await AuthService.getAccessToken();

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || `Request failed: ${response.status}`);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  async listServers(params?: {
    category?: string;
    status?: string;
    search?: string;
  }): Promise<PaginatedResponse<McpServer>> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set('category', params.category);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.search) searchParams.set('search', params.search);

    const query = searchParams.toString();
    const path = `/servers${query ? `?${query}` : ''}`;

    return this.request<PaginatedResponse<McpServer>>(path);
  }

  async getServer(serverId: string): Promise<McpServer> {
    return this.request<McpServer>(`/servers/${serverId}`);
  }

  async createServer(data: {
    name: string;
    description: string;
    runtimeArn: string;
    tags?: string[];
    category?: McpServer['category'];
  }): Promise<McpServer> {
    return this.request<McpServer>('/servers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateServer(
    serverId: string,
    data: Partial<McpServer>
  ): Promise<McpServer> {
    return this.request<McpServer>(`/servers/${serverId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteServer(serverId: string): Promise<void> {
    await this.request<void>(`/servers/${serverId}`, {
      method: 'DELETE',
    });
  }

  async getTools(serverId: string, refresh = false): Promise<ToolsResponse> {
    const query = refresh ? '?refresh=true' : '';
    return this.request<ToolsResponse>(`/servers/${serverId}/tools${query}`);
  }

  async refreshTools(serverId: string): Promise<ToolsResponse> {
    return this.request<ToolsResponse>(`/servers/${serverId}/tools/refresh`, {
      method: 'POST',
    });
  }
}

export const RegistryService = new RegistryServiceClass();
