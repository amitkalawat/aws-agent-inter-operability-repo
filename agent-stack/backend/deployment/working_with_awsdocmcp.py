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
import base64
import boto3
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.tools.code_interpreter_client import code_session

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
    
    
    


# Global instances
mcp_manager = MCPManager()
model_id = "eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
model = BedrockModel(model_id=model_id)
app = BedrockAgentCoreApp()

# Code Interpreter configuration
CODE_INTERPRETER_REGION = 'eu-central-1'
SESSION_CHECK_INTERVAL = 300  # Check every 5 minutes

# Initialize S3 client for saving visualizations
s3_client = boto3.client('s3', region_name='eu-central-1')
VISUALIZATION_BUCKET = 'acme-athena-results-241533163649'  # Using existing Athena results bucket


@tool
def execute_code_with_visualization(
    code: str, 
    description: str = "Execute Python code for data analysis and visualization"
) -> str:
    """Execute Python code using code_session context manager for visualization.
    Supports pandas and matplotlib for creating charts and analyzing data."""
    
    print(f"🔍 DEBUG: Entering execute_code_with_visualization")
    print(f"🔍 DEBUG: Code length: {len(code)} characters")
    print(f"🔍 DEBUG: Description: {description}")
    
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
    
    print(f"🔍 DEBUG: Modified code length: {len(modified_code)} characters")
    print(f"🔍 DEBUG: Modified code preview: {modified_code[:200]}...")
    
    try:
        print(f"🔍 DEBUG: Creating code_session for region: {CODE_INTERPRETER_REGION}")
        with code_session(CODE_INTERPRETER_REGION) as code_client:
            print(f"🔍 DEBUG: code_session created successfully")
            
            response = code_client.invoke("executeCode", {
                "code": modified_code,
                "language": "python",
                "clearContext": False
            })
            
            print(f"🔍 DEBUG: Response received, type: {type(response)}")
            print(f"🔍 DEBUG: Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            
            # Process streaming response
            event_count = 0
            for event in response.get("stream", []):
                event_count += 1
                print(f"🔍 DEBUG: Processing event #{event_count}: {type(event)}")
                print(f"🔍 DEBUG: Event keys: {list(event.keys()) if isinstance(event, dict) else 'Not a dict'}")
                
                if "result" in event:
                    result = event["result"]
                    print(f"🔍 DEBUG: Found result in event, type: {type(result)}")
                    print(f"🔍 DEBUG: Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    
                    # Check for image data in output (try structuredContent.stdout first, then content)
                    output_text = ""
                    print(f"🔍 DEBUG: Starting output extraction...")
                    
                    if isinstance(result, dict):
                        # Try structuredContent.stdout first (official AWS format)
                        structured_content = result.get("structuredContent", {})
                        print(f"🔍 DEBUG: structuredContent type: {type(structured_content)}")
                        if isinstance(structured_content, dict):
                            stdout_text = structured_content.get("stdout", "")
                            print(f"🔍 DEBUG: structuredContent.stdout length: {len(stdout_text)}")
                            if stdout_text:
                                output_text = stdout_text
                                print(f"🔍 DEBUG: Using structuredContent.stdout")
                        
                        # Fallback to content[0].text if no structuredContent
                        if not output_text and "content" in result and result["content"]:
                            content = result["content"]
                            print(f"🔍 DEBUG: content type: {type(content)}, length: {len(content) if isinstance(content, list) else 'Not list'}")
                            content_item = content[0] if isinstance(content, list) and len(content) > 0 else content
                            if isinstance(content_item, dict):
                                content_text = content_item.get("text", "")
                                print(f"🔍 DEBUG: content[0].text length: {len(content_text)}")
                                if content_text:
                                    output_text = content_text
                                    print(f"🔍 DEBUG: Using content[0].text")
                        
                        # Final fallback to generic "output" field (our old approach)
                        if not output_text:
                            generic_output = result.get("output", "")
                            print(f"🔍 DEBUG: generic output length: {len(generic_output)}")
                            if generic_output:
                                output_text = generic_output
                                print(f"🔍 DEBUG: Using generic output")
                    
                    print(f"🔍 DEBUG: Final output_text length: {len(output_text)}")
                    print(f"🔍 DEBUG: Looking for IMAGE_DATA in output...")
                    
                    if output_text and "IMAGE_DATA:" in output_text:
                        print(f"🔍 DEBUG: IMAGE_DATA found! Extracting image data...")
                        # Extract base64 image
                        image_start = output_text.find("IMAGE_DATA:") + 11
                        image_data = output_text[image_start:].strip()
                        
                        print(f"🔍 DEBUG: Extracted image data length: {len(image_data)}")
                        print(f"🔍 DEBUG: Image data preview: {image_data[:50]}...")
                        
                        # Upload to S3
                        s3_url = None
                        try:
                            print(f"🔍 DEBUG: Starting S3 upload...")
                            image_bytes = base64.b64decode(image_data)
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            s3_key = f"visualizations/{timestamp}_chart.png"
                            
                            print(f"🔍 DEBUG: Uploading to S3 bucket: {VISUALIZATION_BUCKET}, key: {s3_key}")
                            s3_client.put_object(
                                Bucket=VISUALIZATION_BUCKET,
                                Key=s3_key,
                                Body=image_bytes,
                                ContentType='image/png'
                            )
                            
                            print(f"🔍 DEBUG: S3 upload successful, generating presigned URL...")
                            s3_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={'Bucket': VISUALIZATION_BUCKET, 'Key': s3_key},
                                ExpiresIn=86400
                            )
                            
                            print(f"🔍 DEBUG: Presigned URL generated: {s3_url}")
                                
                        except Exception as s3_error:
                            print(f"❌ DEBUG: S3 upload failed: {s3_error}")
                            import traceback
                            traceback.print_exc()
                        
                        response_data = {
                            "type": "visualization",
                            "format": "png",
                            "status": "success"
                        }
                        
                        if s3_url:
                            response_data["s3_url"] = s3_url
                            response_data["message"] = f"📊 Visualization created successfully. Use this URL in markdown: ![Chart]({s3_url})"
                        else:
                            # Fallback if S3 upload fails - provide data URL
                            response_data["message"] = f"Visualization created but S3 upload failed. Here's the data URL: ![Chart](data:image/png;base64,{image_data})"
                        
                        print(f"🔍 DEBUG: Returning visualization response: {len(json.dumps(response_data))} characters")
                        return json.dumps(response_data)
                    else:
                        print(f"🔍 DEBUG: No IMAGE_DATA found in output")
                        if output_text:
                            print(f"🔍 DEBUG: Output preview: {output_text[:200]}...")
                    
                    print(f"🔍 DEBUG: Returning raw result")
                    return json.dumps(result)
            
            print(f"🔍 DEBUG: Processed {event_count} events, no results found")
            return "Code executed successfully"
            
    except Exception as e:
        print(f"❌ DEBUG: Exception in execute_code_with_visualization: {e}")
        print(f"❌ DEBUG: Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        return json.dumps({
            "type": "error",
            "message": f"Code execution failed: {str(e)}",
            "status": "failed"
        })


def create_agent_with_memory(payload: dict) -> Tuple[Agent, Any, MCPClient, MCPClient, MCPClient]:
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
    
    # Create MCP client for AWS documentation only
    aws_docs_client = None
    
    try:
        # Try to create AWS documentation client
        aws_docs_client = mcp_manager.create_aws_docs_client()
    except Exception as e:
        print(f"⚠️  Could not initialize AWS documentation client: {e}")
    
    if aws_docs_client:
        # Create agent with context-aware system prompt
        base_prompt = """You're a helpful AI assistant powered by Claude for ACME Corp. You can search and read AWS documentation to help with cloud questions, recommend AWS services, and provide comprehensive answers based on official AWS documentation.

I have access to our previous conversations, so I can maintain context and continuity across our chat sessions. Feel free to engage in natural conversation and ask follow-up questions - I'll remember what we've discussed!

🚨 CRITICAL SQL QUERY INSTRUCTIONS - READ FIRST 🚨
===============================================
BEFORE writing ANY SQL query, you MUST:
1. Check the "Ready-to-Use Query Templates" section below FIRST
2. If a template matches your question, use it EXACTLY as provided
3. Do NOT explore schema or try different approaches if a template exists
4. Only modify templates if absolutely necessary

READY-TO-USE QUERY TEMPLATES:
-----------------------------
❓ "How many people watched movies in last 2 hours?" → USE THIS EXACT QUERY:
SELECT COUNT(DISTINCT t.customer_id) as unique_viewers
FROM acme_telemetry.telemetry t 
JOIN acme_streaming_data.titles ti ON t.title_id = ti.title_id
WHERE ti.title_type = 'movie' 
  AND t.event_type = 'start'
  AND from_iso8601_timestamp(t.event_timestamp) >= current_timestamp - INTERVAL '2' HOUR

❓ "What content types are being watched today?" → USE THIS EXACT QUERY:
SELECT ti.title_type, COUNT(DISTINCT t.customer_id) as viewers
FROM acme_telemetry.telemetry t 
JOIN acme_streaming_data.titles ti ON t.title_id = ti.title_id
WHERE t.event_type = 'start'
  AND from_iso8601_timestamp(t.event_timestamp) >= current_date
GROUP BY ti.title_type

MANDATORY RULES FOR ALL QUERIES:
- Always use from_iso8601_timestamp(event_timestamp) for time filtering (handles ISO8601 with Z timezone)
- Always use lowercase: event_type = 'start', title_type = 'movie'
- For real-time data, always use acme_telemetry database
- For historical data, use acme_streaming_data database

Available capabilities:
- Search AWS documentation for services, best practices, and configuration guides
- Provide comprehensive answers with official AWS documentation sources

ACME Corp Data Schema Information:
=================================

DATABASE: acme_streaming_data (Historical Data)
-----------------------------------------------
1. campaigns (35 columns): Advertising campaign data
   - Identifiers: campaign_id, campaign_name, advertiser_id, advertiser_name
   - Campaign details: industry, campaign_type, objective, start_date, end_date, status
   - Budget: daily_budget, total_budget, spent_amount
   - Targeting: target_age_groups, target_genders, target_countries, target_genres, target_subscription_tiers
   - Ad format: ad_format, ad_duration_seconds, placement_type, creative_url, landing_page_url
   - Metrics: impressions, unique_viewers, clicks, conversions, view_through_rate, click_through_rate, conversion_rate
   - Costs: cost_per_mille, cost_per_click, cost_per_conversion
   - Timestamps: created_at, updated_at

2. customers (21 columns): Customer demographics and subscription data
   - Identity: customer_id, email, first_name, last_name, date_of_birth, age_group
   - Subscription: subscription_tier, subscription_start_date, subscription_end_date
   - Location: country, state, city, timezone
   - Financial: payment_method, monthly_revenue, lifetime_value
   - Status: is_active, acquisition_channel, preferred_genres
   - Timestamps: created_at, updated_at

3. telemetry (24 columns): Historical viewing telemetry events
   - Event data: event_id, customer_id, title_id, session_id, event_type (VARCHAR: 'start', 'pause', 'resume', 'stop', 'complete'), event_timestamp (VARCHAR in ISO8601 format - use from_iso8601_timestamp(event_timestamp) for date operations)
   - Viewing: watch_duration_seconds, position_seconds, completion_percentage
   - Device: device_type, device_id, device_os, app_version
   - Quality: quality, bandwidth_mbps, buffering_events, buffering_duration_seconds, error_count
   - Network: ip_address, country, state, city, isp, connection_type

4. titles (27 columns): Content catalog and metadata
   - Identity: title_id, title_name, title_type (VARCHAR: 'movie', 'series', 'documentary'), genre, sub_genre, content_rating
   - Details: release_date, duration_minutes, season_number, episode_number
   - Production: production_country, original_language, available_languages, director, cast, production_studio
   - Ratings: popularity_score, critical_rating, viewer_rating
   - Business: budget_millions, revenue_millions, awards_count, is_original, licensing_cost
   - Timestamps: created_at, updated_at

DATABASE: acme_telemetry (Real-time Data)
-----------------------------------------
1. telemetry (24 columns): Real-time streaming events (same schema as historical telemetry)
2. video_telemetry_json (24 columns): JSON-formatted real-time telemetry (same schema)

SCHEMA REFERENCE (for custom queries only):
-----------------------------------------
- Use from_iso8601_timestamp(event_timestamp) for time filtering
- Use lowercase values: event_type = 'start', title_type = 'movie'
- Real-time data: acme_telemetry database
- Historical data: acme_streaming_data database

Additional Capability: Data Visualization & Code Execution
========================================================
I can now create charts and visualizations from your data:
- Generate bar charts, line graphs, scatter plots, heatmaps
- Create statistical visualizations from Athena query results
- Export charts as images and save them to S3 for persistent storage
- Perform advanced data analysis with Python libraries

When you EXPLICITLY ask for visualizations, charts, or graphs, I'll:
1. Query your data using Athena tools
2. Process the results with pandas in a secure code interpreter
3. Create professional charts with matplotlib (DO NOT use seaborn - use only matplotlib)
4. Automatically save the visualization to S3 with a shareable URL
5. Return both the image data and persistent S3 link for easy access

Visualization trigger phrases (ONLY create charts when these are used):
- "Show me a bar chart..." or "Create a bar chart..."
- "Create a line graph..." or "Plot a line graph..."
- "Generate a heatmap..." or "Show me a heatmap..."
- "Plot..." or "Graph..." or "Visualize..."
- "Create a chart..." or "Generate a visualization..."

Key guidelines:
- Search AWS documentation when needed to provide accurate, up-to-date information
- For AWS documentation responses: Keep initial responses concise (2-3 key points) unless user requests detailed information
- IMPORTANT: Only use code interpreter for visualizations when explicitly requested (e.g., "show me a chart", "create a graph", "visualize", "plot")
- For data queries without visualization requests (e.g., "give me breakdown", "show me data", "what are the numbers"), return results as formatted text/tables
- CRITICAL: When creating visualizations, use ONLY matplotlib for charts (never use seaborn, plotly, or other libraries)
- Reference the schema above when writing SQL queries or analyzing data
- When asked about ACME data, use the appropriate database: acme_streaming_data for historical analysis, acme_telemetry for real-time data
- Include source URLs when referencing AWS documentation
- Use bullet points for lists and clear formatting"""
        
        # Add conversation context if available
        system_prompt = base_prompt + conversation_context if conversation_context else base_prompt
        
        # Return clients for handling in main logic
        return None, memory_hooks, aws_docs_client, system_prompt
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
        
        return agent, memory_hooks, None, system_prompt


def strands_agent_bedrock(payload):
    """Main entrypoint for the ACME Corp chatbot with AWS documentation support"""
    user_input = payload.get("prompt")
    print("User input:", user_input)
    
    # Create or configure agent with memory for this session
    agent, memory_hooks, aws_docs_client, system_prompt = create_agent_with_memory(payload)
    
    try:
        # Check if AWS docs client is available
        all_tools = [execute_code_with_visualization]  # Always include code interpreter
        
        # Simple single client handling
        if aws_docs_client:
            with aws_docs_client:
                aws_tools = aws_docs_client.list_tools_sync()
                all_tools = aws_tools + [execute_code_with_visualization]
                
                print(f"🛠️  Agent configured with {len(aws_tools)} AWS docs tools")
                print(f"🛠️  Agent configured with 1 code interpreter tool")
                
                agent = Agent(model=model, tools=all_tools, system_prompt=system_prompt)
                response = agent(user_input)
        else:
            # Fallback: only code interpreter
            print(f"🛠️  Fallback agent configured with 1 code interpreter tool only")
            agent = Agent(model=model, tools=[execute_code_with_visualization], system_prompt=system_prompt)
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
    agent, memory_hooks, aws_docs_client, system_prompt = create_agent_with_memory(payload)
    
    try:
        full_response = ""
        
        # Simple single client handling
        if aws_docs_client:
            with aws_docs_client:
                aws_tools = aws_docs_client.list_tools_sync()
                all_tools = aws_tools + [execute_code_with_visualization]
                
                print(f"🛠️  Streaming agent configured with {len(aws_tools)} AWS docs tools")
                
                streaming_agent = Agent(model=model, tools=all_tools, system_prompt=system_prompt)
                
                async for event in streaming_agent.stream_async(user_input):
                    chunk = extract_text_from_event(event)
                    if chunk:
                        full_response += chunk
                        yield chunk
        else:
            # Fallback: only code interpreter
            print(f"🛠️  Fallback streaming agent configured with code interpreter only")
            streaming_agent = Agent(model=model, tools=[execute_code_with_visualization], system_prompt=system_prompt)
            
            async for event in streaming_agent.stream_async(user_input):
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

