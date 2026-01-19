#!/usr/bin/env python3
"""
AWS Documentation Agent using Strands and MCP
"""
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

def get_bearer_token():
    """Get bearer token from Cognito"""
    import requests
    
    pool_id = os.getenv('COGNITO_POOL_ID')
    region = os.getenv('COGNITO_REGION', 'eu-central-1')
    client_id = os.getenv('COGNITO_CLIENT_ID')
    client_secret = os.getenv('COGNITO_CLIENT_SECRET')
    
    if not all([pool_id, client_id, client_secret]):
        raise ValueError("Missing Cognito configuration in .env file")
    
    domain = f"mcp-registry-241533163649-mcp-gateway-registry.auth.{region}.amazoncognito.com"
    token_url = f"https://{domain}/oauth2/token"
    
    response = requests.post(
        token_url,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'mcp-registry/read mcp-registry/write'
        }
    )
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to get bearer token: {response.status_code}")

def create_aws_docs_transport(bearer_token):
    """Create AWS Documentation MCP transport"""
    aws_docs_url = "https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aeu-central-1%3A241533163649%3Aruntime%2Faws_documentation_mcp_server-cBUSt78Z86/invocations?qualifier=DEFAULT"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    return streamablehttp_client(aws_docs_url, headers=headers)

def main():
    print("Starting AWS Documentation Agent...")
    
    bearer_token = get_bearer_token()
    
    bedrock_model = BedrockModel(
        model_id="eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name='eu-central-1',
        temperature=0.3,
    )
    
    client = MCPClient(lambda: create_aws_docs_transport(bearer_token))
    
    with client:
        tools = client.list_tools_sync()
        print(f"Loaded {len(tools)} tools: {[getattr(tool, 'tool_name', 'Unknown') for tool in tools]}")
        
        agent = Agent(
            model=bedrock_model,
            tools=tools,
            system_prompt="""You are an AWS Documentation assistant. Provide concise, accurate answers using the available tools. 

Key guidelines:
- Be brief and to the point
- Use bullet points for lists
- Include only essential information
- Always cite source URLs
- Avoid lengthy explanations unless specifically requested

Use tools to search, read, and recommend AWS documentation as needed."""
        )
        
        print("\nAWS Documentation Agent ready. Type 'quit' to exit.")
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            try:
                async def stream_response():
                    stream = agent.stream_async(user_input)
                    async for event in stream:
                        if "message" in event and "content" in event["message"] and "role" in event["message"] and event["message"]["role"] == "assistant":
                            for content_item in event['message']['content']:
                                if "toolUse" in content_item and "input" in content_item["toolUse"] and content_item["toolUse"]['name'] == 'search_documentation':
                                    print(f"[Searching: {content_item['toolUse']['input']['search_phrase']}]")
                                elif "toolUse" in content_item and "name" in content_item["toolUse"] and content_item["toolUse"]['name'] == 'read_documentation':
                                    print(f"[Reading: {content_item['toolUse']['input']['url']}]")
                                elif "toolUse" in content_item and "name" in content_item["toolUse"] and content_item["toolUse"]['name'] == 'recommend':
                                    print(f"[Getting recommendations: {content_item['toolUse']['input']['url']}]")
                        elif "data" in event:
                            print(event['data'], end="", flush=True)
                
                print("Response: ", end="", flush=True)
                asyncio.run(stream_response())
                print()
                        
            except Exception as e:
                print(f"Error: {e}")
                response = agent(user_input)
                print(f"Response: {response.message}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Failed to start agent: {e}")
        print("Make sure your .env file is configured correctly")