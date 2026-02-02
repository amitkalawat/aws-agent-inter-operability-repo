#!/usr/bin/env python3
"""
ACME Corp Bedrock AgentCore Chatbot with AWS Documentation MCP Integration
CDK-managed deployment version
"""

import argparse
import json
import hashlib
import requests
import time
import base64
import boto3
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.tools.code_interpreter_client import code_session

from memory_manager import create_memory_manager, extract_session_info
from secrets_manager import secrets_manager


# Configuration from environment
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-haiku-4-5-20250414-v1:0')


def get_mcp_gateway_endpoint() -> Optional[str]:
    """
    Get MCP Gateway endpoint from environment variable (set by CDK).
    Gateway provides a unified endpoint for all MCP servers.

    Returns the Gateway endpoint URL if configured, None otherwise.
    """
    gateway_endpoint = os.environ.get('MCP_GATEWAY_ENDPOINT')
    if gateway_endpoint:
        print(f"MCP Gateway endpoint configured: {gateway_endpoint[:80]}...")
        return gateway_endpoint
    return None


def extract_text_from_event(event) -> str:
    """Extract text content from Strands streaming event structure"""
    if not event:
        return ""

    try:
        if isinstance(event, dict):
            if any(key in event for key in ['init_event_loop', 'start', 'start_event_loop', 'role', 'content']):
                return ""

            if 'event' in event:
                inner_event = event['event']
                if isinstance(inner_event, dict) and 'contentBlockDelta' in inner_event:
                    delta = inner_event['contentBlockDelta']
                    if isinstance(delta, dict) and 'delta' in delta:
                        delta_content = delta['delta']
                        if isinstance(delta_content, dict) and 'text' in delta_content:
                            text = delta_content['text']
                            return str(text) if text is not None else ""
                return ""

            if 'callback' in event:
                callback_data = event['callback']
                if isinstance(callback_data, str):
                    return callback_data
                elif isinstance(callback_data, dict) and 'text' in callback_data:
                    text = callback_data['text']
                    return str(text) if text is not None else ""
                return ""

            if 'text' in event and len(event) == 1:
                text_value = event['text']
                return str(text_value) if text_value is not None else ""
            return ""

        if isinstance(event, str) and event.strip():
            return event

    except Exception as e:
        print(f"Warning: Error extracting text from event: {e}")

    return ""


class MCPManager:
    """
    Manages MCP Gateway client creation and bearer token authentication.

    Uses AgentCore Gateway for unified access to all MCP tools.
    """

    def __init__(self):
        self._bearer_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._credentials: Optional[Dict[str, str]] = None
        self._mcp_available: bool = False
        self._initialized: bool = False
        self._gateway_endpoint: Optional[str] = None

    def _init_credentials(self) -> bool:
        """Initialize credentials and check if MCP Gateway is available"""
        if self._initialized:
            return self._mcp_available

        self._initialized = True

        try:
            # Get Cognito credentials from secrets (for OAuth bearer token)
            self._credentials = secrets_manager.get_mcp_credentials()

            # Get Gateway endpoint from environment
            self._gateway_endpoint = get_mcp_gateway_endpoint()

            if self._gateway_endpoint:
                self._mcp_available = True
                print("MCP Gateway configured - unified endpoint for all MCP tools")
            else:
                print("MCP Gateway endpoint not configured")
                self._mcp_available = False

        except Exception as e:
            print(f"Could not initialize MCP Gateway: {e}")
            self._mcp_available = False

        return self._mcp_available

    def is_mcp_available(self) -> bool:
        """Check if MCP Gateway integration is available"""
        return self._init_credentials()

    def _get_bearer_token(self) -> str:
        """Get bearer token from Cognito with caching"""
        if not self._init_credentials():
            raise Exception("MCP Gateway not available")

        current_time = time.time()

        if self._bearer_token and current_time < self._token_expires_at:
            return self._bearer_token

        try:
            region = self._credentials['MCP_COGNITO_REGION']
            client_id = self._credentials['MCP_COGNITO_CLIENT_ID']
            client_secret = self._credentials['MCP_COGNITO_CLIENT_SECRET']

            cognito_domain = self._credentials.get('MCP_COGNITO_DOMAIN')
            if not cognito_domain:
                raise Exception("MCP_COGNITO_DOMAIN not configured in secrets")

            token_url = f"https://{cognito_domain}/oauth2/token"

            print(f"Getting fresh MCP bearer token from {region}...")

            response = requests.post(
                token_url,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'scope': 'mcp/invoke'
                },
                timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                self._bearer_token = token_data['access_token']
                self._token_expires_at = current_time + (50 * 60)
                print("MCP bearer token obtained successfully")
                return self._bearer_token
            else:
                raise Exception(f"Token request failed: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Failed to get MCP bearer token: {e}")
            raise

    def create_gateway_transport(self):
        """Create MCP transport for Gateway"""
        try:
            if not self._gateway_endpoint:
                raise Exception("Gateway endpoint not configured")

            bearer_token = self._get_bearer_token()
            headers = {
                "authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }

            print(f"Creating Gateway MCP transport: {self._gateway_endpoint[:80]}...")
            return streamablehttp_client(
                self._gateway_endpoint,
                headers=headers,
                timeout=120,
                terminate_on_close=False
            )
        except Exception as e:
            print(f"Failed to create Gateway transport: {e}")
            raise

    def create_gateway_client(self) -> MCPClient:
        """Create unified MCP client for Gateway (all tools in one client)"""
        try:
            print("Initializing MCP Gateway client...")
            client = MCPClient(lambda: self.create_gateway_transport())
            print("MCP Gateway client initialized successfully")
            return client
        except Exception as e:
            print(f"Failed to create Gateway MCP client: {e}")
            raise


# Global instances
mcp_manager = MCPManager()
model = BedrockModel(model_id=BEDROCK_MODEL_ID)
app = BedrockAgentCoreApp()

# S3 client for visualizations
s3_client = boto3.client('s3', region_name=AWS_REGION)
VISUALIZATION_BUCKET = os.environ.get('VISUALIZATION_BUCKET', 'acme-visualizations')


@tool
def execute_code_with_visualization(
    code: str,
    description: str = "Execute Python code for data analysis and visualization"
) -> str:
    """Execute Python code using code_session context manager for visualization."""

    if description:
        code = f"# {description}\n{code}"

    modified_code = f"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

{code}

if 'plt' in locals() and plt.get_fignums():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close('all')
    print(f"IMAGE_DATA:{{image_base64}}")
"""

    try:
        with code_session(AWS_REGION) as code_client:
            response = code_client.invoke("executeCode", {
                "code": modified_code,
                "language": "python",
                "clearContext": False
            })

            for event in response.get("stream", []):
                if "result" in event:
                    result = event["result"]

                    output_text = ""
                    if isinstance(result, dict):
                        structured_content = result.get("structuredContent", {})
                        if isinstance(structured_content, dict):
                            output_text = structured_content.get("stdout", "")

                        if not output_text and "content" in result and result["content"]:
                            content = result["content"]
                            content_item = content[0] if isinstance(content, list) else content
                            if isinstance(content_item, dict):
                                output_text = content_item.get("text", "")

                    if output_text and "IMAGE_DATA:" in output_text:
                        image_start = output_text.find("IMAGE_DATA:") + 11
                        image_data = output_text[image_start:].strip()

                        s3_url = None
                        try:
                            image_bytes = base64.b64decode(image_data)
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            s3_key = f"visualizations/{timestamp}_chart.png"

                            s3_client.put_object(
                                Bucket=VISUALIZATION_BUCKET,
                                Key=s3_key,
                                Body=image_bytes,
                                ContentType='image/png'
                            )

                            s3_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={'Bucket': VISUALIZATION_BUCKET, 'Key': s3_key},
                                ExpiresIn=86400
                            )
                        except Exception as s3_error:
                            print(f"S3 upload failed: {s3_error}")

                        response_data = {
                            "type": "visualization",
                            "format": "png",
                            "status": "success"
                        }

                        if s3_url:
                            response_data["s3_url"] = s3_url
                            response_data["message"] = f"Visualization created successfully. URL: {s3_url}"

                        return json.dumps(response_data)

                    return json.dumps(result)

            return "Code executed successfully"

    except Exception as e:
        return json.dumps({
            "type": "error",
            "message": f"Code execution failed: {str(e)}",
            "status": "failed"
        })


def get_system_prompt(conversation_context: str = "") -> str:
    """Generate the system prompt with optional conversation context"""

    base_prompt = """You're a helpful AI assistant powered by Claude for ACME Corp. You can search AWS documentation, analyze data, and help with cloud questions.

Available capabilities:
- Search AWS documentation for services, best practices, and configuration guides
- Query and analyze ACME Corp streaming data using Athena SQL
- Execute Python code for data visualization (charts, graphs, plots)

Key guidelines:
- Search AWS documentation when needed to provide accurate, up-to-date information
- Keep responses concise unless detailed information is requested
- Reference the data schema when writing SQL queries
- Include source URLs when referencing AWS documentation

CHART/VISUALIZATION GENERATION (execute_code_with_visualization tool):
When asked to create charts, graphs, or data visualizations, use the execute_code_with_visualization tool with matplotlib code.

Example code for a bar chart:
```python
import matplotlib.pyplot as plt

data = {'Jan': 45000, 'Feb': 52000, 'Mar': 48000, 'Apr': 61000, 'May': 58000, 'Jun': 72000}
months = list(data.keys())
values = list(data.values())

plt.figure(figsize=(10, 6))
plt.bar(months, values, color='steelblue')
plt.xlabel('Month')
plt.ylabel('Sales ($)')
plt.title('Monthly Sales Data')
plt.tight_layout()
```

The tool will:
1. Execute the matplotlib code
2. Save the chart to S3
3. Return a presigned URL

CRITICAL: When the tool returns a response with "s3_url", you MUST include the COMPLETE URL in your response using markdown: ![Chart Description](complete-s3-url-with-all-parameters)

The URL will be long (500+ characters) with query parameters like X-Amz-Signature - this is expected. Never truncate it."""

    return base_prompt + conversation_context if conversation_context else base_prompt


def create_agent_with_memory(payload: dict) -> Tuple[Agent, Any, list, str]:
    """Create agent instance with memory configuration and MCP clients"""

    session_id, actor_id = extract_session_info(payload)
    user_input = payload.get("prompt", "")

    memory_name = f"ACMEChatMemory_{hashlib.md5(actor_id.encode()).hexdigest()[:8]}"

    print(f"Configuring memory: session={session_id}, actor={actor_id}")

    memory_hooks = None
    conversation_context = ""

    try:
        memory_hooks = create_memory_manager(
            memory_name=memory_name,
            actor_id=actor_id,
            session_id=session_id,
            region=AWS_REGION
        )

        conversation_context = memory_hooks.retrieve_conversation_context(user_input)
        print("Memory manager configured successfully")

    except Exception as e:
        print(f"Could not configure memory: {e}")

    # Initialize MCP Gateway client (unified access to all MCP tools)
    mcp_clients = []

    if mcp_manager.is_mcp_available():
        try:
            gateway_client = mcp_manager.create_gateway_client()
            mcp_clients.append(('gateway', gateway_client))
            print("MCP Gateway client ready - unified access to all MCP tools")
        except Exception as e:
            print(f"MCP Gateway client unavailable: {e}")
    else:
        print("MCP Gateway not configured - agent running without MCP tools")

    system_prompt = get_system_prompt(conversation_context)

    return None, memory_hooks, mcp_clients, system_prompt


def strands_agent_bedrock(payload):
    """Main entrypoint for the ACME Corp chatbot"""
    user_input = payload.get("prompt")
    print("User input:", user_input)

    agent, memory_hooks, mcp_clients, system_prompt = create_agent_with_memory(payload)

    try:
        all_tools = [execute_code_with_visualization]

        # Build context managers dynamically based on available clients
        if mcp_clients:
            # Use nested context managers for all available clients
            clients_to_use = [client for _, client in mcp_clients]

            def run_with_clients(clients, idx=0):
                if idx >= len(clients):
                    # All clients entered, now collect tools and run
                    for name, client in mcp_clients:
                        try:
                            tools = client.list_tools_sync()
                            all_tools.extend(tools)
                            print(f"Added {len(tools)} tools from {name}")
                        except Exception as e:
                            print(f"Could not get tools from {name}: {e}")

                    agent = Agent(model=model, tools=all_tools, system_prompt=system_prompt)
                    return agent(user_input)
                else:
                    with clients[idx]:
                        return run_with_clients(clients, idx + 1)

            response = run_with_clients(clients_to_use)
        else:
            agent = Agent(model=model, tools=all_tools, system_prompt=system_prompt)
            response = agent(user_input)

        assistant_response = response.message['content'][0]['text']

        if memory_hooks:
            try:
                memory_hooks.save_chat_interaction(user_input, assistant_response)
            except Exception as e:
                print(f"Could not save interaction to memory: {e}")

        return assistant_response

    except Exception as e:
        print(f"Error during agent execution: {e}")
        return "I apologize, but I encountered an error while processing your request. Please try again."


async def strands_agent_bedrock_streaming(payload):
    """Async streaming entrypoint for real-time responses"""
    user_input = payload.get("prompt")
    print("User input (streaming):", user_input)

    agent, memory_hooks, mcp_clients, system_prompt = create_agent_with_memory(payload)

    try:
        full_response = ""
        all_tools = [execute_code_with_visualization]

        if mcp_clients:
            clients_to_use = [client for _, client in mcp_clients]

            async def run_streaming_with_clients(clients, idx=0):
                nonlocal full_response
                if idx >= len(clients):
                    for name, client in mcp_clients:
                        try:
                            tools = client.list_tools_sync()
                            all_tools.extend(tools)
                        except Exception:
                            pass

                    streaming_agent = Agent(model=model, tools=all_tools, system_prompt=system_prompt)

                    async for event in streaming_agent.stream_async(user_input):
                        chunk = extract_text_from_event(event)
                        if chunk:
                            full_response += chunk
                            yield chunk
                else:
                    with clients[idx]:
                        async for chunk in run_streaming_with_clients(clients, idx + 1):
                            yield chunk

            async for chunk in run_streaming_with_clients(clients_to_use):
                yield chunk
        else:
            streaming_agent = Agent(model=model, tools=all_tools, system_prompt=system_prompt)
            async for event in streaming_agent.stream_async(user_input):
                chunk = extract_text_from_event(event)
                if chunk:
                    full_response += chunk
                    yield chunk

        if memory_hooks:
            try:
                memory_hooks.save_chat_interaction(user_input, full_response)
            except Exception as e:
                print(f"Could not save streaming interaction to memory: {e}")

    except Exception as e:
        print(f"Error during streaming agent execution: {e}")
        yield f"Error: {str(e)}"


@app.entrypoint
async def strands_agent_bedrock_unified(payload, context=None):
    """Unified entrypoint that routes between streaming and non-streaming"""

    streaming_enabled = False

    if payload and isinstance(payload, dict):
        streaming_enabled = payload.get("streaming", False)

    if context and hasattr(context, 'request'):
        query_params = str(context.request.url.query) if hasattr(context.request, 'url') else ""
        streaming_enabled = streaming_enabled or "streaming=true" in query_params

        if hasattr(context.request, 'headers'):
            accept_header = context.request.headers.get('accept', '')
            streaming_enabled = streaming_enabled or 'text/event-stream' in accept_header

    if streaming_enabled:
        return strands_agent_bedrock_streaming(payload)
    else:
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
