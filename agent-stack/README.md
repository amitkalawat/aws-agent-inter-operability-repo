# Agent Stack

AI agent infrastructure built with AWS Bedrock AgentCore and MCP (Model Context Protocol) integration.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│   React App     │────▶│  Bedrock AgentCore   │────▶│  MCP Gateway     │
│   (CloudFront)  │     │  (Claude Haiku 4.5)  │     │  (Semantic Search)│
└─────────────────┘     └──────────────────────┘     └────────┬─────────┘
        │                        │                            │
        ▼                        ▼                   ┌────────▼─────────┐
┌─────────────────┐     ┌──────────────────────┐     │   MCP Servers    │
│  AWS Cognito    │     │  AgentCore Memory    │     │  (Cognito OAuth) │
│  (Auth)         │     │  (Conversation)      │     │  - AWS Docs      │
└─────────────────┘     └──────────────────────┘     │  - Data Process  │
                                                     └──────────────────┘
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
- MCP Gateway (semantic search, OAuth outbound auth via Token Vault)
- 2 MCP Servers (AWS Docs, Data Processing)
- AgentCore Memory (with summarization strategy)
- OAuth Provider (Token Vault credential provider)
- S3 + CloudFront for frontend

### MCP Servers (`aws-mcp-server-agentcore/`)
Model Context Protocol servers:
- **AWS Documentation** - Search AWS docs
- **Data Processing** - Athena SQL queries on telemetry data

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
│   │       ├── gateway-construct.ts
│   │       ├── mcp-server-construct.ts
│   │       ├── memory-construct.ts
│   │       ├── oauth-provider-construct.ts
│   │       └── secrets-construct.ts
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
    └── aws-dataprocessing-mcp-server/
```

## Deployment

> **For deployment instructions, see the [main README](../README.md) in the repository root.**
>
> The main README contains the complete step-by-step deployment guide with verification checks.

## Configuration

- **Region**: us-west-2
- **Model**: Claude Haiku 4.5 (via inference profile)
- **Authentication**: AWS Cognito with JWT

## Features

- **Conversation Memory**: Persistent conversation history via AgentCore Memory (with summarization strategy)
- **MCP Gateway**: Unified tool access via AgentCore Gateway with semantic search and OAuth outbound auth
- **MCP Integration**: 2 MCP servers for AWS docs and Athena data queries
- **Streaming Responses**: Real-time response streaming
- **Code Interpreter**: Python code execution for data visualization

## Logs

```bash
# Agent logs (log group has -DEFAULT suffix)
aws logs tail /aws/bedrock-agentcore/runtimes/acme_chatbot-GMG3nr6fes-DEFAULT --region us-west-2 --since 10m --format short

# Filter for real errors (exclude OTEL noise)
aws logs tail /aws/bedrock-agentcore/runtimes/acme_chatbot-GMG3nr6fes-DEFAULT --region us-west-2 --since 10m --format short 2>&1 | grep -v 'otel-rt-logs' | grep -iE 'ERROR|WARN|Exception|fail|denied'

# MCP server logs
aws logs tail /aws/bedrock-agentcore/runtimes/dataproc_mcp-86MK1VGnew-DEFAULT --region us-west-2 --since 10m --format short
aws logs tail /aws/bedrock-agentcore/runtimes/aws_docs_mcp-KBewiR60Fg-DEFAULT --region us-west-2 --since 10m --format short
```

## Outputs

After deployment, CDK outputs:
- `FrontendUrl` - CloudFront URL for the chat app
- `AgentArn` - Main agent runtime ARN
- `CognitoUserPoolId` - User pool for authentication
- `CognitoAppClientId` - App client ID for frontend
- `GatewayId` - MCP Gateway ID
- `MemoryId` - AgentCore Memory ID
