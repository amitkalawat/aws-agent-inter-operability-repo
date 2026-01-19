#!/usr/bin/env python3
"""
AWS Documentation Tools using MCP
Wrapper functions for integrating AWS Documentation MCP server with Strands agent
"""

import asyncio
import time
import requests
import uuid
from typing import Dict, Any, Optional
from strands import tool
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from secrets_manager import secrets_manager


class AWSDocsMCPManager:
    """Manager for AWS Documentation MCP integration"""
    
    def __init__(self):
        self._credentials: Optional[Dict[str, str]] = None
        self._bearer_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._client: Optional[MCPClient] = None
        self._tools_cache: Optional[list] = None
        self._initialized = False
    
    def _load_credentials(self) -> Dict[str, str]:
        """Load MCP credentials from AWS Secrets Manager"""
        if self._credentials is None:
            self._credentials = secrets_manager.get_mcp_credentials()
        return self._credentials
    
    def _get_bearer_token(self) -> str:
        """Get bearer token from Cognito with caching"""
        current_time = time.time()
        
        # Check if we have a valid cached token
        if self._bearer_token and current_time < self._token_expires_at:
            return self._bearer_token
        
        # Get fresh token
        try:
            credentials = self._load_credentials()
            
            pool_id = credentials['MCP_COGNITO_POOL_ID']
            region = credentials['MCP_COGNITO_REGION']
            client_id = credentials['MCP_COGNITO_CLIENT_ID']
            client_secret = credentials['MCP_COGNITO_CLIENT_SECRET']
            
            domain = f"mcp-registry-241533163649-mcp-gateway-registry.auth.{region}.amazoncognito.com"
            token_url = f"https://{domain}/oauth2/token"
            
            print(f"🔑 Getting fresh MCP bearer token from {region}...")
            
            response = requests.post(
                token_url,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'scope': 'mcp-registry/read mcp-registry/write'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self._bearer_token = token_data['access_token']
                # Cache for 50 minutes (tokens typically valid for 1 hour)
                self._token_expires_at = current_time + (50 * 60)
                print("✅ MCP bearer token obtained successfully")
                return self._bearer_token
            else:
                raise Exception(f"Token request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Failed to get MCP bearer token: {e}")
            raise
    
    def _create_transport(self):
        """Create AWS Documentation MCP transport"""
        credentials = self._load_credentials()
        bearer_token = self._get_bearer_token()
        
        aws_docs_url = credentials['MCP_DOCS_URL']
        headers = {"Authorization": f"Bearer {bearer_token}"}
        
        return streamablehttp_client(aws_docs_url, headers=headers)
    
    def _get_client(self) -> MCPClient:
        """Get or create MCP client"""
        if not self._initialized or self._client is None:
            print("🔧 Initializing AWS Documentation MCP client...")
            self._client = MCPClient(lambda: self._create_transport())
            self._initialized = True
        
        return self._client
    
    def _list_tools_sync(self):
        """List available tools synchronously"""
        if self._tools_cache is not None:
            return self._tools_cache
        
        async def _list_tools():
            client = self._get_client()
            with client:
                tools = client.list_tools_sync()
                return tools
        
        try:
            self._tools_cache = asyncio.run(_list_tools())
            print(f"✅ Loaded {len(self._tools_cache)} AWS Documentation tools")
            return self._tools_cache
        except Exception as e:
            print(f"❌ Failed to list MCP tools: {e}")
            raise
    


# Global manager instance
_aws_docs_manager = AWSDocsMCPManager()


def get_aws_docs_mcp_client():
    """
    Get configured MCP client for AWS Documentation tools
    
    Returns:
        MCPClient instance if available, None if disabled
    """
    try:
        print("🚀 Initializing AWS Documentation MCP integration...")
        
        # Test credentials loading
        _aws_docs_manager._load_credentials()
        
        # Test token acquisition  
        _aws_docs_manager._get_bearer_token()
        
        # Get the MCP client
        client = _aws_docs_manager._get_client()
        print("✅ AWS Documentation MCP client initialized successfully")
        
        return client
        
    except Exception as e:
        print(f"⚠️  AWS Documentation MCP client initialization failed: {e}")
        print("ℹ️  AWS documentation features will be disabled")
        return None


def get_aws_docs_tools():
    """
    Get direct MCP tools for AWS Documentation (not wrapped)
    
    Returns:
        List of MCP tool objects if available, empty list if disabled
    """
    try:
        client = get_aws_docs_mcp_client()
        if client is None:
            return []
        
        with client:
            tools = client.list_tools_sync()
            tool_names = [getattr(tool, 'name', 'Unknown') for tool in tools]
            print(f"✅ Loaded {len(tools)} direct MCP tools: {', '.join(tool_names)}")
            return tools
            
    except Exception as e:
        print(f"⚠️  Failed to get AWS documentation tools: {e}")
        return []