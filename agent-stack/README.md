# Agent Stack

AI agent infrastructure built with AWS Bedrock AgentCore and MCP (Model Context Protocol) integration.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   React App     │────▶│  Bedrock AgentCore   │────▶│   MCP Servers   │
│   (CloudFront)  │     │  (Claude Haiku 4.5)  │     │  (4 servers)    │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
        │                        │
        ▼                        ▼
┌─────────────────┐     ┌──────────────────────┐
│  AWS Cognito    │     │  AgentCore Memory    │
│  (Auth)         │     │  (Conversation)      │
└─────────────────┘     └──────────────────────┘
```

## Components

### Frontend (`frontend/acme-chat/`)
React TypeScript application with:
- AWS Cognito authentication
- Real-time chat interface
- Streaming response support
- Image rendering (S3 presigned URLs)

### CDK Infrastructure (`cdk/`)
AWS CDK stack that deploys:
- Cognito User Pool for authentication
- Main Agent Runtime (Claude Haiku 4.5)
- 4 MCP Servers
- AgentCore Memory
- S3 + CloudFront for frontend

### MCP Servers (`aws-mcp-server-agentcore/`)
Model Context Protocol servers:
- **AWS Documentation** - Search AWS docs
- **Data Processing** - Athena SQL queries
- **Rekognition** - Image analysis
- **Nova Canvas** - Image generation

## Project Structure

```
agent-stack/
├── cdk/                          # CDK infrastructure
│   ├── lib/
│   │   ├── acme-stack.ts         # Main stack
│   │   ├── config/               # Configuration
│   │   └── constructs/           # CDK constructs
│   │       ├── agent-runtime-construct.ts
│   │       ├── cognito-construct.ts
│   │       ├── frontend-construct.ts
│   │       ├── mcp-server-construct.ts
│   │       └── memory-construct.ts
│   └── docker/
│       └── agent/                # Agent container
│           ├── strands_claude.py # Main agent code
│           └── Dockerfile
├── frontend/
│   └── acme-chat/                # React TypeScript app
│       └── src/
│           ├── components/       # React components
│           └── services/         # API services
└── aws-mcp-server-agentcore/     # MCP server implementations
    ├── aws-documentation-mcp-server/
    ├── aws-dataprocessing-mcp-server/
    ├── amazon-rekognition-mcp-server/
    └── nova-canvas-mcp-server/
```

## Deployment

### Prerequisites
- Node.js 18+
- AWS CLI configured
- AWS CDK installed (`npm install -g aws-cdk`)

### Deploy Everything

```bash
cd cdk

# Install dependencies
npm install

# Build frontend
cd ../frontend/acme-chat
npm install
npm run build
cd ../../cdk

# Deploy stack
cdk deploy
```

## Configuration

- **Region**: us-west-2
- **Model**: Claude Haiku 4.5 (via inference profile)
- **Authentication**: AWS Cognito with JWT

## Features

- **Conversation Memory**: Persistent conversation history via AgentCore Memory
- **MCP Integration**: 4 MCP servers for AWS docs, data queries, image analysis, and image generation
- **Streaming Responses**: Real-time response streaming
- **Code Interpreter**: Python code execution for data visualization
- **Image Support**: Generate images (Nova Canvas) and analyze them (Rekognition)

## Logs

```bash
# Agent logs
aws logs tail /aws/bedrock-agentcore/runtimes/acme_chatbot-RB6voZDbJ7-DEFAULT --region us-west-2 --since 10m

# MCP server logs (example: Rekognition)
aws logs tail /aws/bedrock-agentcore/runtimes/rekognition_mcp-EFnVxZ5ZKO-DEFAULT --region us-west-2 --since 10m
```

## Outputs

After deployment, CDK outputs:
- `FrontendUrl` - CloudFront URL for the chat app
- `AgentArn` - Main agent runtime ARN
- `CognitoUserPoolId` - User pool for authentication
- `CognitoAppClientId` - App client ID for frontend
