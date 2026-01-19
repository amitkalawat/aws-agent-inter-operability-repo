#!/usr/bin/env python3
"""
Bedrock Agent with Nova Canvas MCP Server - CloudFront URL Mode
Uses the latest deployed MCP server that returns CloudFront URLs
"""
import os
import re
import logging
import webbrowser
import requests
from datetime import datetime
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables
load_dotenv()

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

def get_bearer_token():
    """Get bearer token from Cognito"""
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

def create_nova_canvas_transport(bearer_token):
    """Create Nova Canvas transport using hardcoded URL"""
    nova_canvas_url = "https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aeu-central-1%3A241533163649%3Aruntime%2Fnova_canvas_s3_mcp_server-UdNTVPHZ5T/invocations?qualifier=DEFAULT"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    return streamablehttp_client(nova_canvas_url, headers=headers)

def extract_image_urls(text):
    """Extract CloudFront URLs from text response"""
    cloudfront_pattern = r'https://[a-zA-Z0-9.-]+\.cloudfront\.net/[^\s\n]+'
    urls = re.findall(cloudfront_pattern, text)
    return urls

def display_and_open_images(urls):
    """Display image URLs in a clean format and optionally open them"""
    if not urls:
        return
    
    print(f"\n🖼️ Generated {len(urls)} image(s):")
    print("=" * 60)
    
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    print("=" * 60)
    
    # Ask user if they want to open images in browser
    if urls:
        try:
            response = input(f"\n🌐 Open image(s) in browser? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                for url in urls:
                    webbrowser.open(url)
                print(f"✅ Opened {len(urls)} image(s) in browser")
        except KeyboardInterrupt:
            print("\n⏭️ Skipping browser open")
        except Exception as e:
            print(f"⚠️ Could not open browser: {e}")



def main():
    print("🚀 Starting Nova Canvas Agent...")
    
    # Get bearer token from Cognito
    print("🔐 Getting bearer token...")
    bearer_token = get_bearer_token()
    print("✅ Bearer token obtained")
    
    # Create Bedrock model
    bedrock_model = BedrockModel(
        model_id="eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name='eu-central-1',
        temperature=0.3,
    )
    
    # Create Nova Canvas MCP client
    print("🔗 Creating Nova Canvas MCP client...")
    client = MCPClient(lambda: create_nova_canvas_transport(bearer_token))
    
    print("🤖 Starting agent with Nova Canvas tools...")
    
    # CRITICAL: Follow the exact pattern from the working example
    with client:
        # Get the tools from the MCP server
        tools = client.list_tools_sync()
        print(f"✅ Tools loaded: {len(tools)} tools available")
        for tool in tools:
            tool_name = getattr(tool, 'tool_name', 'Unknown')
            # Try to get description from tool_spec if available
            tool_desc = 'No description'
            if hasattr(tool, 'tool_spec') and hasattr(tool.tool_spec, 'description'):
                tool_desc = tool.tool_spec.description
            print(f"   - {tool_name}: {str(tool_desc)[:100]}...")
        
        # Create an Agent with the model and tools
        agent = Agent(
            model=bedrock_model,
            tools=tools,
            system_prompt="""You are a Nova Canvas image generation assistant.

CRITICAL INSTRUCTIONS:
- For ANY image, picture, drawing, or visual content request, you MUST use the generate_image tool
- NEVER describe images without generating them
- NEVER provide fake URLs or placeholder responses
- ALWAYS use the actual tools provided

Available tools:
- generate_image: Generate images with Nova Canvas (returns CloudFront URLs)
- generate_image_with_colors: Generate images with specific color palettes

RESPONSE FORMAT:
When you generate images, you MUST respond with ONLY a JSON object in this exact format:
{"image_urls": ["https://cloudfront-url-1", "https://cloudfront-url-2"]}

For single images: {"image_urls": ["https://cloudfront-url"]}
For multiple images: {"image_urls": ["https://url1", "https://url2", "https://url3"]}

PROCESS:
1. Call generate_image with detailed, descriptive prompts
2. Extract the CloudFront URLs from the tool response
3. Return ONLY the JSON object with the URLs
4. Do NOT include any other text, explanations, or descriptions

You MUST use the tools and return JSON format for any image request!
"""
        )
        
        print(f"🎯 Agent created with tools: {[getattr(tool, 'tool_name', 'Unknown') for tool in tools]}")
        
        print("\n🎯 Nova Canvas Agent ready! Type 'quit' to exit.")
        
        while True:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            try:
                print("🤖 Response: ", end="", flush=True)
                response = agent(user_input)
                response_text = str(response.message)
                print(response_text)
                
                # Try to parse JSON response for image URLs
                image_urls = []
                try:
                    import json
                    # Look for JSON pattern in the response
                    json_pattern = r'\{"image_urls":\s*\[([^\]]+)\]\}'
                    json_match = re.search(json_pattern, response_text)
                    if json_match:
                        json_str = json_match.group(0)
                        parsed_json = json.loads(json_str)
                        if 'image_urls' in parsed_json:
                            image_urls = parsed_json['image_urls']
                            print(f"\n✅ Parsed {len(image_urls)} image URL(s) from JSON response")
                    else:
                        # Fallback to regex extraction
                        image_urls = extract_image_urls(response_text)
                        if image_urls:
                            print(f"\n✅ Extracted {len(image_urls)} image URL(s) using regex fallback")
                except Exception as e:
                    print(f"\n⚠️ JSON parsing error: {e}, trying regex extraction...")
                    image_urls = extract_image_urls(response_text)
                    if image_urls:
                        print(f"\n✅ Extracted {len(image_urls)} image URL(s) using regex fallback")
                
                if image_urls:
                    display_and_open_images(image_urls)
                elif any(word in user_input.lower() for word in ['image', 'picture', 'photo', 'generate', 'create', 'draw', 'cat', 'dog']):
                    print(f"\n⚠️ No image URLs found. The tool may not have been called properly.")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        print("💡 Make sure your .env file is configured correctly")