#!/usr/bin/env python3
"""
Test DataProcessing MCP directly with correct URL format
"""

import requests
import boto3
import json
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import sys

def get_oauth_token():
    """Get OAuth token using client credentials"""
    client = boto3.client('cognito-idp', region_name='eu-central-1')
    
    # Get credentials from Secrets Manager
    secrets_client = boto3.client('secretsmanager', region_name='eu-central-1')
    response = secrets_client.get_secret_value(SecretId='acme-chatbot/mcp-credentials')
    credentials = json.loads(response['SecretString'])
    
    # Get OAuth token
    try:
        auth_response = client.initiate_auth(
            ClientId=credentials['MCP_COGNITO_CLIENT_ID'],
            AuthFlow='USER_SRP_AUTH',
            AuthParameters={
                'USERNAME': credentials['MCP_COGNITO_CLIENT_ID'],
                'SRP_A': 'dummy'
            }
        )
    except:
        # Try admin auth flow
        try:
            import hmac
            import hashlib
            import base64
            
            secret = credentials['MCP_COGNITO_CLIENT_SECRET']
            message = credentials['MCP_COGNITO_CLIENT_ID']
            secret_hash = base64.b64encode(
                hmac.new(
                    secret.encode(),
                    message.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()
            
            # Admin auth not available, try client credentials
            # Construct token endpoint
            token_endpoint = f"https://cognito-idp.{credentials['MCP_COGNITO_REGION']}.amazonaws.com/"
            
            # Use AWS SDK to get token
            from warrant import AWSSRP
            
            # Fall back to direct HTTP request
            import urllib.parse
            token_url = f"https://mcp-gateway-registry.auth.{credentials['MCP_COGNITO_REGION']}.amazoncognito.com/oauth2/token"
            
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': credentials['MCP_COGNITO_CLIENT_ID'],
                'client_secret': credentials['MCP_COGNITO_CLIENT_SECRET']
            }
            
            token_response = requests.post(
                token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if token_response.status_code == 200:
                return token_response.json()['access_token']
            else:
                print(f"Token request failed: {token_response.status_code} - {token_response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting token: {e}")
            return None

def test_dataproc_urls():
    """Test different URL formats for DataProcessing MCP"""
    
    # Get OAuth token
    token = get_oauth_token()
    if not token:
        print("Failed to get OAuth token")
        return
    
    print(f"✅ Got OAuth token: {token[:20]}...")
    
    # Test different URL formats
    test_urls = [
        # Current malformed URL
        "https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/dataproc_mcp_ibcv3-vwsZvUBHMP/invocations",
        
        # Properly formatted with ARN
        "https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aeu-central-1%3A241533163649%3Aruntime%2Fdataproc_mcp_ibcv3-vwsZvUBHMP/invocations?qualifier=DEFAULT",
        
        # Without qualifier
        "https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aeu-central-1%3A241533163649%3Aruntime%2Fdataproc_mcp_ibcv3-vwsZvUBHMP/invocations"
    ]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test payload
    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "0.1.0",
            "capabilities": {}
        },
        "id": 1
    }
    
    for url in test_urls:
        print(f"\n🧪 Testing URL: {url[:100]}...")
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Success! Response: {response.text[:200]}")
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_list_tools():
    """Test listing tools with correct URL"""
    token = get_oauth_token()
    if not token:
        print("Failed to get OAuth token")
        return
    
    # Use the correct ARN format
    url = "https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aeu-central-1%3A241533163649%3Aruntime%2Fdataproc_mcp_ibcv3-vwsZvUBHMP/invocations?qualifier=DEFAULT"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Initialize session
    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "0.1.0",
            "capabilities": {}
        },
        "id": 1
    }
    
    print("\n🔧 Initializing MCP session...")
    response = requests.post(url, json=init_payload, headers=headers, timeout=10)
    print(f"Init response: {response.status_code} - {response.text[:200]}")
    
    if response.status_code == 200:
        # List tools
        tools_payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        print("\n📋 Listing tools...")
        response = requests.post(url, json=tools_payload, headers=headers, timeout=10)
        print(f"Tools response: {response.status_code}")
        if response.status_code == 200:
            tools_data = response.json()
            if 'result' in tools_data and 'tools' in tools_data['result']:
                tools = tools_data['result']['tools']
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools[:5]:
                    print(f"   - {tool.get('name', 'unknown')}")
            else:
                print(f"Response: {response.text}")

if __name__ == "__main__":
    print("🧪 Testing DataProcessing MCP Connection")
    print("="*50)
    
    print("\n1. Testing different URL formats...")
    test_dataproc_urls()
    
    print("\n2. Testing tool listing with correct URL...")
    test_list_tools()