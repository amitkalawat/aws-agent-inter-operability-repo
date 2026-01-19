#!/usr/bin/env python3
"""MCP Server for Nova Act Browser Tool Integration"""

import asyncio
import json
import threading
import concurrent.futures
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from bedrock_agentcore.tools.browser_client import browser_session
from nova_act import NovaAct
from rich.console import Console
import sys
sys.path.append("./interactive_tools")
from browser_viewer import BrowserViewerServer

console = Console()

class NovaActMCPServer:
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.server = Server("nova-act-browser")
        self.browser_client = None
        self.nova_act = None
        self.viewer = None
        self.ws_url = None
        self.headers = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.setup_tools()

    def setup_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="start_browser_session",
                    description="Start browser session with live viewer",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "nova_act_key": {"type": "string", "description": "Nova Act API key"},
                            "starting_page": {"type": "string", "description": "Initial URL to load"}
                        },
                        "required": ["nova_act_key", "starting_page"]
                    }
                ),
                Tool(
                    name="browser_action",
                    description="Execute browser automation using natural language",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "Natural language instruction for browser automation"}
                        },
                        "required": ["prompt"]
                    }
                ),
                Tool(
                    name="stop_browser_session",
                    description="Stop browser session and cleanup resources",
                    inputSchema={"type": "object", "properties": {}}
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "start_browser_session":
                return await self._start_browser_session(arguments)
            elif name == "browser_action":
                return await self._browser_action(arguments)
            elif name == "stop_browser_session":
                return await self._stop_browser_session()
            else:
                raise ValueError(f"Unknown tool: {name}")

    def _start_browser_session_sync(self, args: Dict[str, Any]) -> str:
        """Synchronous browser session start"""
        nova_act_key = args["nova_act_key"]
        starting_page = args["starting_page"]
        
        # Create browser session
        self.browser_client = browser_session(self.region).__enter__()
        self.ws_url, self.headers = self.browser_client.generate_ws_headers()
        
        # Start viewer server
        self.viewer = BrowserViewerServer(self.browser_client, port=8000)
        viewer_url = self.viewer.start(open_browser=True)
        
        # Initialize Nova Act
        self.nova_act = NovaAct(
            cdp_endpoint_url=self.ws_url,
            cdp_headers=self.headers,
            nova_act_api_key=nova_act_key,
            starting_page=starting_page,
        ).__enter__()
        
        return f"Browser session started successfully!\nLive viewer: {viewer_url}\nReady for automation commands."

    async def _start_browser_session(self, args: Dict[str, Any]) -> List[TextContent]:
        """Start browser session with Nova Act and live viewer"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, self._start_browser_session_sync, args)
            # Wait for page to fully load
            await asyncio.sleep(5)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error starting browser session: {str(e)}")]

    def _browser_action_sync(self, prompt: str) -> str:
        """Synchronous browser action"""
        result = self.nova_act.act(prompt)
        return f"Action completed successfully!\nResult: {result}"

    async def _browser_action(self, args: Dict[str, Any]) -> List[TextContent]:
        """Execute browser automation"""
        if not self.nova_act:
            return [TextContent(type="text", text="Browser session not started. Use start_browser_session first.")]
        
        try:
            prompt = args["prompt"]
            # Wait a moment before action
            await asyncio.sleep(2)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, self._browser_action_sync, prompt)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing browser action: {str(e)}")]

    def _stop_browser_session_sync(self) -> str:
        """Synchronous browser session stop"""
        if self.nova_act:
            self.nova_act.__exit__(None, None, None)
            self.nova_act = None
        
        if self.browser_client:
            self.browser_client.stop()
            self.browser_client = None
        
        return "Browser session stopped successfully."

    async def _stop_browser_session(self) -> List[TextContent]:
        """Stop browser session and cleanup"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, self._stop_browser_session_sync)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error stopping browser session: {str(e)}")]

    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

if __name__ == "__main__":
    console.print("[green]🚀 Starting Nova Act MCP Server...[/green]")
    server = NovaActMCPServer()
    console.print("[cyan]📡 MCP Server ready for connections[/cyan]")
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        console.print("[yellow]🛑 MCP Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ MCP Server error: {e}[/red]")