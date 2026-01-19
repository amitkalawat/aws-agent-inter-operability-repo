# AgentCore Browser Tool with Nova Act

Standalone MCP (Model Context Protocol) implementation for browser automation using Nova Act and AWS Bedrock AgentCore.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python3 mcp_client_example.py
```

## What it does

- **Starts MCP Server**: Automatically launches browser MCP server
- **Browser Session**: Creates AWS AgentCore browser session with live viewer
- **Nova Act Integration**: Natural language browser automation
- **Live Viewer**: Real-time browser viewing at http://localhost:8000
- **Cleanup**: Automatic resource cleanup on exit

## Files

- `mcp_client_example.py` - Main client (starts server automatically)
- `browser_mcp_server.py` - MCP server with Nova Act integration
- `interactive_tools/browser_viewer.py` - Live browser viewer
- `requirements.txt` - Python dependencies

## Usage

1. Run the client
2. Enter starting URL (default: https://www.imdb.com/)
3. Enter automation prompt (e.g., "Extract the main page title")
4. Watch automation in live viewer
5. Results displayed in terminal

## MCP Tools Available

- `start_browser_session` - Initialize browser with live viewer
- `browser_action` - Execute natural language automation
- `stop_browser_session` - Cleanup resources

## Requirements

- AWS credentials configured
- Nova Act API key
- Python 3.8+
- Required packages in requirements.txt