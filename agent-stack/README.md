# Agent Stack

AI agent infrastructure built with AWS Bedrock AgentCore and MCP (Model Context Protocol) integration.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   React App     │────▶│  Bedrock AgentCore   │────▶│   MCP Servers   │
│   (CloudFront)  │     │  (Claude 3.7 Sonnet) │     │  (AWS Docs/Data)│
└─────────────────┘     └──────────────────────┘     └─────────────────┘
        │                        │
        ▼                        ▼
┌─────────────────┐     ┌──────────────────────┐
│  AWS Cognito    │     │  AgentCore Memory    │
│  (Auth)         │     │  (Conversation)      │
└─────────────────┘     └──────────────────────┘
```

## Components

### Frontend (`frontend/`)
React TypeScript application with:
- AWS Cognito authentication
- Real-time chat interface
- Streaming response support
- Session management

### Backend (`backend/`)
Python Strands agent with:
- Claude 3.7 Sonnet model
- AgentCore Memory for conversation persistence
- Calculator tool (SymPy)
- Weather tool
- Dual MCP integration

### Infrastructure (`infrastructure/`)
- Cognito User Pool configuration
- Authentication setup

### MCP Servers (`aws-mcp-server-agentcore/`)
Model Context Protocol servers for:
- AWS Documentation search
- Data Processing (Athena SQL queries)

## Project Structure

```
agent-stack/
├── backend/
│   ├── agent/                    # Agent source code
│   │   ├── strands_claude.py     # Main agent
│   │   ├── memory_manager.py     # Memory implementation
│   │   └── requirements.txt      # Python dependencies
│   └── deployment/               # Deployment scripts and config
├── frontend/
│   └── acme-chat/                # React TypeScript app
├── infrastructure/
│   └── cognito/                  # Cognito setup
└── aws-mcp-server-agentcore/     # MCP server implementations
```

## Deployment

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS CLI configured

### Deploy Agent

```bash
# Step 1: Copy agent files to deployment directory
cd backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/memory_manager.py .
cp ../agent/requirements.txt .

# Step 2: Deploy
source .venv/bin/activate
python deploy_agent_with_auth.py
```

### Deploy Frontend

```bash
cd frontend/acme-chat
npm install
npm run build
```

## Configuration

- **Region**: eu-central-1 (Frankfurt)
- **Model**: Claude 3.7 Sonnet
- **Authentication**: AWS Cognito with JWT

## Features

- **Conversation Memory**: Persistent conversation history
- **MCP Integration**: AWS Documentation + Data Processing
- **Streaming Responses**: Real-time response streaming
- **Session Management**: Per-user session tracking

## Logs

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/strands_claude_getting_started_auth-nYQSK477I1-DEFAULT --region eu-central-1 --since 10m
```

See `CLAUDE.md` for detailed deployment instructions and troubleshooting.