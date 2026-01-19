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
    """Manages MCP client creation and bearer token authentication"""

    def __init__(self):
        self._bearer_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._credentials: Optional[Dict[str, str]] = None
        self._mcp_available: bool = False
        self._initialized: bool = False

    def _init_credentials(self) -> bool:
        """Initialize credentials and check if MCP is available"""
        if self._initialized:
            return self._mcp_available

        self._initialized = True
        try:
            self._credentials = secrets_manager.get_mcp_credentials()
            # Check if any MCP URL is configured
            mcp_urls = ['MCP_DOCS_URL', 'MCP_DATAPROC_URL', 'MCP_REKOGNITION_URL', 'MCP_NOVA_CANVAS_URL']
            available_urls = [url for url in mcp_urls if self._credentials.get(url)]
            if available_urls:
                self._mcp_available = True
                print(f"MCP integration available with URLs: {available_urls}")
            else:
                print("MCP URLs not configured in secrets - MCP integration disabled")
                self._mcp_available = False
        except Exception as e:
            print(f"Could not load MCP credentials: {e}")
            self._mcp_available = False

        return self._mcp_available

    def is_mcp_available(self) -> bool:
        """Check if MCP integration is available"""
        return self._init_credentials()

    def _get_bearer_token(self) -> str:
        """Get bearer token from Cognito with caching"""
        if not self._init_credentials():
            raise Exception("MCP not available - no URLs configured")

        current_time = time.time()

        if self._bearer_token and current_time < self._token_expires_at:
            return self._bearer_token

        try:
            pool_id = self._credentials['MCP_COGNITO_POOL_ID']
            region = self._credentials['MCP_COGNITO_REGION']
            client_id = self._credentials['MCP_COGNITO_CLIENT_ID']
            client_secret = self._credentials['MCP_COGNITO_CLIENT_SECRET']

            # Check if MCP_COGNITO_DOMAIN is configured, otherwise skip bearer token
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
                    'scope': 'mcp-registry/read mcp-registry/write'
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

    def create_mcp_transport(self, url_key: str):
        """Create MCP transport for a given URL key"""
        try:
            credentials = secrets_manager.get_mcp_credentials()
            bearer_token = self._get_bearer_token()

            if url_key not in credentials or not credentials[url_key]:
                raise Exception(f"{url_key} not configured in secrets")

            mcp_url = credentials[url_key]
            headers = {"Authorization": f"Bearer {bearer_token}"}

            return streamablehttp_client(mcp_url, headers=headers)
        except Exception as e:
            print(f"Failed to create MCP transport for {url_key}: {e}")
            raise

    def create_aws_docs_client(self) -> MCPClient:
        """Create MCP client for AWS Documentation"""
        try:
            print("Initializing AWS Documentation MCP client...")
            client = MCPClient(lambda: self.create_mcp_transport('MCP_DOCS_URL'))
            print("AWS Documentation MCP client initialized successfully")
            return client
        except Exception as e:
            print(f"Failed to create AWS docs MCP client: {e}")
            raise

    def create_dataproc_client(self) -> MCPClient:
        """Create MCP client for DataProcessing"""
        try:
            print("Initializing DataProcessing MCP client...")
            client = MCPClient(lambda: self.create_mcp_transport('MCP_DATAPROC_URL'))
            print("DataProcessing MCP client initialized successfully")
            return client
        except Exception as e:
            print(f"Failed to create dataproc MCP client: {e}")
            raise

    def create_rekognition_client(self) -> MCPClient:
        """Create MCP client for Rekognition"""
        try:
            print("Initializing Rekognition MCP client...")
            client = MCPClient(lambda: self.create_mcp_transport('MCP_REKOGNITION_URL'))
            print("Rekognition MCP client initialized successfully")
            return client
        except Exception as e:
            print(f"Failed to create Rekognition MCP client: {e}")
            raise

    def create_nova_canvas_client(self) -> MCPClient:
        """Create MCP client for Nova Canvas"""
        try:
            print("Initializing Nova Canvas MCP client...")
            client = MCPClient(lambda: self.create_mcp_transport('MCP_NOVA_CANVAS_URL'))
            print("Nova Canvas MCP client initialized successfully")
            return client
        except Exception as e:
            print(f"Failed to create Nova Canvas MCP client: {e}")
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

    base_prompt = """You're a helpful AI assistant powered by Claude for ACME Corp. You can search AWS documentation, analyze data, generate images, and help with cloud questions.

Available capabilities:
- Search AWS documentation for services, best practices, and configuration guides
- Query and analyze ACME Corp streaming data using Athena SQL
- Generate images using Amazon Nova Canvas
- Analyze images using Amazon Rekognition
- Execute Python code for data visualization

Key guidelines:
- Search AWS documentation when needed to provide accurate, up-to-date information
- Keep responses concise unless detailed information is requested
- Reference the data schema when writing SQL queries
- Include source URLs when referencing AWS documentation"""

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

    # Collect available MCP clients (only if MCP is configured)
    mcp_clients = []

    if mcp_manager.is_mcp_available():
        try:
            mcp_clients.append(('aws_docs', mcp_manager.create_aws_docs_client()))
        except Exception as e:
            print(f"AWS docs client unavailable: {e}")

        try:
            mcp_clients.append(('dataproc', mcp_manager.create_dataproc_client()))
        except Exception as e:
            print(f"DataProcessing client unavailable: {e}")

        try:
            mcp_clients.append(('rekognition', mcp_manager.create_rekognition_client()))
        except Exception as e:
            print(f"Rekognition client unavailable: {e}")

        try:
            mcp_clients.append(('nova_canvas', mcp_manager.create_nova_canvas_client()))
        except Exception as e:
            print(f"Nova Canvas client unavailable: {e}")
    else:
        print("MCP integration not configured - agent running without MCP tools")

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
