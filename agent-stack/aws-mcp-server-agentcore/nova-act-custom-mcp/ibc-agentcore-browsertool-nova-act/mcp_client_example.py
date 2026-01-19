#!/usr/bin/env python3
"""Example MCP client for Nova Act Browser Tool"""

import asyncio
import json
import signal
import subprocess
import atexit
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def cleanup_server():
    """Kill any orphaned MCP server processes"""
    try:
        subprocess.run(['pkill', '-f', 'browser_mcp_server.py'], capture_output=True)
        print("\n🧹 Cleaned up MCP server processes")
    except:
        pass

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n⚠️  Interrupted - cleaning up...")
    cleanup_server()
    exit(0)

async def main():
    """Example usage of Nova Act MCP server"""
    
    # Setup cleanup handlers
    atexit.register(cleanup_server)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Server parameters
        server_params = StdioServerParameters(
            command="python3",
            args=["browser_mcp_server.py"]
        )
        
        print("🚀 Starting MCP client with server cleanup...")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                print("Available tools:")
                for tool in tools.tools:
                    print(f"- {tool.name}: {tool.description}")
                
                # Get user input
                print("\n🌐 Nova Act Browser Tool - MCP Client")
                print("=====================================\n")
                
                starting_page = input("Enter starting page URL (default: https://www.imdb.com/): ").strip()
                if not starting_page:
                    starting_page = "https://www.imdb.com/"
                
                prompt = input("Enter automation prompt: ").strip()
                if not prompt:
                    prompt = "Extract the main page title and first few navigation links"
                
                print(f"\n📋 Configuration:")
                print(f"Starting page: {starting_page}")
                print(f"Prompt: {prompt}\n")
                
                # Start browser session
                print("🚀 Starting browser session...")
                result = await session.call_tool(
                    "start_browser_session",
                    {
                        "nova_act_key": "2468fa87-786a-40aa-8997-58626802fe41",
                        "starting_page": starting_page
                    }
                )
                print(f"Result: {result.content[0].text}")
                
                # Execute browser action
                print("\n🤖 Executing browser automation...")
                result = await session.call_tool(
                    "browser_action",
                    {
                        "prompt": prompt
                    }
                )
                print(f"Result: {result.content[0].text}")
                
                # Stop browser session
                print("\n🛑 Stopping browser session...")
                result = await session.call_tool("stop_browser_session", {})
                print(f"Result: {result.content[0].text}")
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Ensure cleanup happens
        cleanup_server()
        print("✅ MCP client finished")

if __name__ == "__main__":
    asyncio.run(main())