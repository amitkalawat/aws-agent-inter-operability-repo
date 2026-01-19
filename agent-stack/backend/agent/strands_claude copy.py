#!/usr/bin/env python3
"""
ACME Corp Bedrock AgentCore Chatbot with AWS Documentation MCP Integration
Refactored to use the proven working pattern from aws_docs_agent.py
"""

import argparse
import json
import hashlib
import requests
import time
from typing import Any, Dict, Optional, Tuple

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from memory_manager import create_memory_manager, extract_session_info
from secrets_manager import secrets_manager


def extract_text_from_event(event) -> str:
    """Extract text content from Strands streaming event structure"""
    if not event:
        return ""
    
    try:
        # Handle different event structures from Strands
        if isinstance(event, dict):
            # Skip system events that don't contain text
            if any(key in event for key in ['init_event_loop', 'start', 'start_event_loop', 'role', 'content']):
                return ""
            
            # Handle nested event structure: {'event': {'contentBlockDelta': {'delta': {'text': 'content'}}}}
            if 'event' in event:
                inner_event = event['event']
                if isinstance(inner_event, dict) and 'contentBlockDelta' in inner_event:
                    delta = inner_event['contentBlockDelta']
                    if isinstance(delta, dict) and 'delta' in delta:
                        delta_content = delta['delta']
                        if isinstance(delta_content, dict) and 'text' in delta_content:
                            text = delta_content['text']
                            return str(text) if text is not None else ""
                # Skip other event types
                return ""
            
            # Handle Strands callback event structure: {'callback': 'text'}
            if 'callback' in event:
                callback_data = event['callback']
                if isinstance(callback_data, str):
                    return callback_data
                elif isinstance(callback_data, dict) and 'text' in callback_data:
                    text = callback_data['text']
                    return str(text) if text is not None else ""
                # Don't process non-string callbacks to avoid dict concatenation
                return ""
            
            # Only process simple text fields, avoid complex objects
            if 'text' in event and len(event) == 1:  # Only if 'text' is the only key
                text_value = event['text']
                return str(text_value) if text_value is not None else ""
                
            # Skip complex data structures that might cause concatenation errors
            return ""
        
        # If it's a simple string, return it (but avoid empty strings)
        if isinstance(event, str) and event.strip():
            return event
            
    except Exception as e:
        print(f"⚠️  Error extracting text from event: {e}")
        print(f"Event type: {type(event)}")
        print(f"Event structure: {event}")
        # Always return empty string on error to prevent crashes
    
    return ""


class MCPManager:
    """Manages MCP client creation and bearer token authentication"""
    
    def __init__(self):
        self._bearer_token: Optional[str] = None
        self._token_expires_at: float = 0
    
    def _get_bearer_token(self) -> str:
        """Get bearer token from Cognito with caching"""
        current_time = time.time()
        
        # Check if we have a valid cached token
        if self._bearer_token and current_time < self._token_expires_at:
            return self._bearer_token
        
        # Get fresh token from Secrets Manager
        try:
            credentials = secrets_manager.get_mcp_credentials()
            
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
    
    def create_aws_docs_transport(self):
        """Create AWS Documentation MCP transport"""
        try:
            credentials = secrets_manager.get_mcp_credentials()
            bearer_token = self._get_bearer_token()
            
            aws_docs_url = credentials['MCP_DOCS_URL']
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            return streamablehttp_client(aws_docs_url, headers=headers)
        except Exception as e:
            print(f"❌ Failed to create AWS docs MCP transport: {e}")
            raise
    
    def create_dataproc_transport(self):
        """Create DataProcessing MCP transport"""
        try:
            credentials = secrets_manager.get_mcp_credentials()
            bearer_token = self._get_bearer_token()
            
            # Check if dataproc URL is available
            if 'MCP_DATAPROC_URL' not in credentials or not credentials['MCP_DATAPROC_URL']:
                raise Exception("MCP_DATAPROC_URL not configured in secrets")
            
            dataproc_url = credentials['MCP_DATAPROC_URL']
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            return streamablehttp_client(dataproc_url, headers=headers)
        except Exception as e:
            print(f"❌ Failed to create dataproc MCP transport: {e}")
            raise
    
    def create_aws_docs_client(self) -> MCPClient:
        """Create MCP client for AWS Documentation"""
        try:
            print("🔧 Initializing AWS Documentation MCP client...")
            client = MCPClient(lambda: self.create_aws_docs_transport())
            print("✅ AWS Documentation MCP client initialized successfully")
            return client
        except Exception as e:
            print(f"❌ Failed to create AWS docs MCP client: {e}")
            raise
    
    def create_dataproc_client(self) -> MCPClient:
        """Create MCP client for DataProcessing"""
        try:
            print("🔧 Initializing DataProcessing MCP client...")
            client = MCPClient(lambda: self.create_dataproc_transport())
            print("✅ DataProcessing MCP client initialized successfully")
            return client
        except Exception as e:
            print(f"❌ Failed to create dataproc MCP client: {e}")
            raise


# Global instances
mcp_manager = MCPManager()
model_id = "eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
model = BedrockModel(model_id=model_id)
app = BedrockAgentCoreApp()


def create_agent_with_memory(payload: dict) -> Tuple[Agent, Any, MCPClient, MCPClient]:
    """Create agent instance with memory configuration and MCP client"""
    
    # Extract session and user information
    session_id, actor_id = extract_session_info(payload)
    user_input = payload.get("prompt", "")
    
    # Create memory name for this user (must match AWS naming pattern)
    memory_name = f"ACMEChatMemory_{hashlib.md5(actor_id.encode()).hexdigest()[:8]}"
    
    print(f"🧠 Configuring memory: session={session_id}, actor={actor_id}")
    
    # Initialize memory manager
    memory_hooks = None
    conversation_context = ""
    
    try:
        # Create memory manager
        memory_hooks = create_memory_manager(
            memory_name=memory_name,
            actor_id=actor_id,
            session_id=session_id,
            region="eu-central-1"
        )
        
        # Retrieve conversation context for this query
        conversation_context = memory_hooks.retrieve_conversation_context(user_input)
        
        print("✅ Memory manager configured successfully")
        
    except Exception as e:
        print(f"⚠️  Could not configure memory: {e}")
        print("ℹ️  Continuing without memory - conversations won't persist")
    
    # Create MCP clients for AWS documentation and data processing
    aws_docs_client = None
    dataproc_client = None
    
    try:
        # Try to create AWS documentation client
        aws_docs_client = mcp_manager.create_aws_docs_client()
    except Exception as e:
        print(f"⚠️  Could not initialize AWS documentation client: {e}")
    
    try:
        # Try to create dataproc client
        dataproc_client = mcp_manager.create_dataproc_client()
    except Exception as e:
        print(f"⚠️  Could not initialize dataproc client: {e}")
    
    if aws_docs_client or dataproc_client:
        # Create agent with context-aware system prompt
        base_prompt = """You're a helpful AI assistant powered by Claude for ACME Corp. You can search and read AWS documentation to help with cloud questions, recommend AWS services, and provide comprehensive answers based on official AWS documentation.

I also have access to data processing tools that can help with data analysis and processing tasks.

I have access to our previous conversations, so I can maintain context and continuity across our chat sessions. Feel free to engage in natural conversation and ask follow-up questions - I'll remember what we've discussed!

Available capabilities:
- Search AWS documentation for services, best practices, and configuration guides
- Data processing and analysis tools for various data tasks
- Provide comprehensive answers with official AWS documentation sources

Key guidelines:
- Search AWS documentation when needed to provide accurate, up-to-date information
- Use data processing tools for analysis tasks when appropriate
- Be comprehensive but concise in your responses
- Include source URLs when referencing AWS documentation
- Use bullet points for lists and clear formatting"""
        
        # Add conversation context if available
        system_prompt = base_prompt + conversation_context if conversation_context else base_prompt
        
        # Return clients for handling in main logic
        return None, memory_hooks, aws_docs_client, dataproc_client, system_prompt
    else:
        # Fallback: create basic agent without MCP tools
        print("ℹ️  No MCP clients available - falling back to basic agent")
        basic_prompt = """You're a helpful AI assistant powered by Claude for ACME Corp. I can answer general questions and have conversations.

I have access to our previous conversations, so I can maintain context and continuity across our chat sessions."""
        
        system_prompt = basic_prompt + conversation_context if conversation_context else basic_prompt
        
        agent = Agent(
            model=model,
            tools=[],  # No tools in fallback mode
            system_prompt=system_prompt
        )
        
        return agent, memory_hooks, None, None, system_prompt


def strands_agent_bedrock(payload):
    """Main entrypoint for the ACME Corp chatbot with AWS documentation support"""
    user_input = payload.get("prompt")
    print("User input:", user_input)
    
    # Create or configure agent with memory for this session
    agent, memory_hooks, aws_docs_client, dataproc_client, system_prompt = create_agent_with_memory(payload)
    
    try:
        if aws_docs_client and dataproc_client:
            # Use both MCP clients with nested context managers
            with aws_docs_client:
                with dataproc_client:
                    # Get tools from both MCP clients
                    aws_tools = aws_docs_client.list_tools_sync()
                    dataproc_tools = dataproc_client.list_tools_sync()
                    
                    # Combine tools from both servers
                    all_tools = aws_tools + dataproc_tools
                    
                    aws_tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown')) for tool in aws_tools]
                    dataproc_tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown')) for tool in dataproc_tools]
                    
                    print(f"🛠️  Agent configured with {len(aws_tools)} AWS docs tools: {aws_tool_names}")
                    print(f"🛠️  Agent configured with {len(dataproc_tools)} dataproc tools: {dataproc_tool_names}")
                    
                    # Create agent with combined tools
                    agent = Agent(
                        model=model,
                        tools=all_tools,
                        system_prompt=system_prompt
                    )
                    
                    # Process the user input within both MCP client contexts
                    response = agent(user_input)
        elif aws_docs_client:
            # Use only AWS documentation client
            with aws_docs_client:
                tools = aws_docs_client.list_tools_sync()
                tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown')) for tool in tools]
                print(f"🛠️  Agent configured with {len(tools)} AWS documentation tools: {tool_names}")
                
                agent = Agent(
                    model=model,
                    tools=tools,
                    system_prompt=system_prompt
                )
                
                response = agent(user_input)
        elif dataproc_client:
            # Use only dataproc client
            with dataproc_client:
                tools = dataproc_client.list_tools_sync()
                tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown')) for tool in tools]
                print(f"🛠️  Agent configured with {len(tools)} dataproc tools: {tool_names}")
                
                agent = Agent(
                    model=model,
                    tools=tools,
                    system_prompt=system_prompt
                )
                
                response = agent(user_input)
        else:
            # Fallback: use basic agent without MCP tools
            response = agent(user_input)
        
        assistant_response = response.message['content'][0]['text']
        
        # Save the interaction to memory
        if memory_hooks:
            try:
                memory_hooks.save_chat_interaction(user_input, assistant_response)
            except Exception as e:
                print(f"⚠️  Could not save interaction to memory: {e}")
        
        return assistant_response
        
    except Exception as e:
        print(f"❌ Error during agent execution: {e}")
        # Return a helpful error message
        return "I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists."


async def strands_agent_bedrock_streaming(payload):
    """Async streaming entrypoint for the ACME Corp chatbot with real-time responses"""
    user_input = payload.get("prompt")
    print("User input (streaming):", user_input)
    
    # Create or configure agent with memory for this session
    agent, memory_hooks, aws_docs_client, dataproc_client, system_prompt = create_agent_with_memory(payload)
    
    try:
        # Handle different MCP client configurations
        if aws_docs_client and dataproc_client:
            # Use both MCP clients with nested context managers
            with aws_docs_client:
                with dataproc_client:
                    # Get tools from both MCP clients
                    aws_tools = aws_docs_client.list_tools_sync()
                    dataproc_tools = dataproc_client.list_tools_sync()
                    
                    # Combine tools from both servers
                    all_tools = aws_tools + dataproc_tools
                    
                    aws_tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown')) for tool in aws_tools]
                    dataproc_tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown')) for tool in dataproc_tools]
                    
                    print(f"🛠️  Streaming agent configured with {len(aws_tools)} AWS docs tools: {aws_tool_names}")
                    print(f"🛠️  Streaming agent configured with {len(dataproc_tools)} dataproc tools: {dataproc_tool_names}")
                    
                    # Create agent with combined tools
                    streaming_agent = Agent(
                        model=model,
                        tools=all_tools,
                        system_prompt=system_prompt
                    )
                    
                    # Stream responses as they're generated
                    full_response = ""
                    async for event in streaming_agent.stream_async(user_input):
                        # Extract text from Strands streaming event structure
                        chunk = extract_text_from_event(event)
                        if chunk:
                            full_response += chunk
                            yield chunk
                    
                    # Save to memory after streaming is complete
                    if memory_hooks:
                        try:
                            memory_hooks.save_chat_interaction(user_input, full_response)
                        except Exception as e:
                            print(f"⚠️  Could not save streaming interaction to memory: {e}")
                            
        elif aws_docs_client:
            # Use only AWS documentation client
            with aws_docs_client:
                tools = aws_docs_client.list_tools_sync()
                tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown')) for tool in tools]
                print(f"🛠️  Streaming agent configured with {len(tools)} AWS documentation tools: {tool_names}")
                
                streaming_agent = Agent(
                    model=model,
                    tools=tools,
                    system_prompt=system_prompt
                )
                
                # Stream responses
                full_response = ""
                async for event in streaming_agent.stream_async(user_input):
                    # Extract text from Strands streaming event structure
                    chunk = extract_text_from_event(event)
                    if chunk:
                        full_response += chunk
                        yield chunk
                
                # Save to memory
                if memory_hooks:
                    try:
                        memory_hooks.save_chat_interaction(user_input, full_response)
                    except Exception as e:
                        print(f"⚠️  Could not save streaming interaction to memory: {e}")
                        
        elif dataproc_client:
            # Use only dataproc client
            with dataproc_client:
                tools = dataproc_client.list_tools_sync()
                tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown')) for tool in tools]
                print(f"🛠️  Streaming agent configured with {len(tools)} dataproc tools: {tool_names}")
                
                streaming_agent = Agent(
                    model=model,
                    tools=tools,
                    system_prompt=system_prompt
                )
                
                # Stream responses
                full_response = ""
                async for event in streaming_agent.stream_async(user_input):
                    # Extract text from Strands streaming event structure
                    chunk = extract_text_from_event(event)
                    if chunk:
                        full_response += chunk
                        yield chunk
                
                # Save to memory
                if memory_hooks:
                    try:
                        memory_hooks.save_chat_interaction(user_input, full_response)
                    except Exception as e:
                        print(f"⚠️  Could not save streaming interaction to memory: {e}")
        else:
            # Fallback: use basic agent without MCP tools
            full_response = ""
            async for event in agent.stream_async(user_input):
                # Extract text from Strands streaming event structure
                chunk = extract_text_from_event(event)
                if chunk:
                    full_response += chunk
                    yield chunk
            
            # Save to memory
            if memory_hooks:
                try:
                    memory_hooks.save_chat_interaction(user_input, full_response)
                except Exception as e:
                    print(f"⚠️  Could not save streaming interaction to memory: {e}")
        
    except Exception as e:
        print(f"❌ Error during streaming agent execution: {e}")
        # Stream error message
        error_response = {"error": str(e), "type": "stream_error"}
        yield f"❌ Error: {str(e)}"


@app.entrypoint
async def strands_agent_bedrock_unified(payload, context=None):
    """Unified entrypoint that routes between streaming and non-streaming based on request parameters"""
    
    # Debug: Print payload structure
    print(f"🔍 DEBUG: Payload type: {type(payload)}")
    print(f"🔍 DEBUG: Payload content: {payload}")
    
    # Check for streaming parameter in various places
    streaming_enabled = False
    
    # Check payload for streaming flag
    if payload and isinstance(payload, dict):
        streaming_enabled = payload.get("streaming", False)
        print(f"🔍 DEBUG: Found streaming in payload: {streaming_enabled}")
    
    # Check context/request for streaming parameter in query string
    if context and hasattr(context, 'request'):
        # Check query parameters for streaming=true
        query_params = str(context.request.url.query) if hasattr(context.request, 'url') else ""
        streaming_enabled = streaming_enabled or "streaming=true" in query_params
        
        # Also check headers for streaming indication
        if hasattr(context.request, 'headers'):
            accept_header = context.request.headers.get('accept', '')
            streaming_enabled = streaming_enabled or 'text/event-stream' in accept_header
            print(f"🔍 DEBUG: Accept header: {accept_header}")
    
    print(f"🔄 Routing request - streaming_enabled: {streaming_enabled}")
    
    if streaming_enabled:
        print("➡️  Routing to streaming handler")
        # Return async generator for streaming
        return strands_agent_bedrock_streaming(payload)
    else:
        print("➡️  Routing to non-streaming handler")
        # Return direct result for non-streaming
        return strands_agent_bedrock(payload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Strands Agent locally')
    parser.add_argument('payload', help='JSON payload with prompt', nargs='?')
    
    args = parser.parse_args()
    
    if args.payload:
        try:
            payload_data = json.loads(args.payload)
            result = strands_agent_bedrock(payload_data)
            print("Response:", result)
        except json.JSONDecodeError:
            print("Error: Invalid JSON payload")
        except Exception as e:
            print(f"Error: {e}")
    else:
        app.run()