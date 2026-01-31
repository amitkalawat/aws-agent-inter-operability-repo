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
- 2 MCP Servers
- AgentCore Memory
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
    └── aws-dataprocessing-mcp-server/
```

## Deployment

### Prerequisites
- Node.js 18+
- AWS CLI configured with `jq` installed
- AWS CDK installed (`npm install -g aws-cdk`)

### Deploy Everything

**Important**: The frontend requires Cognito configuration that's only available after CDK deployment. Follow these steps in order:

```bash
# 1. Install CDK dependencies
cd cdk
npm install

# 2. Install frontend dependencies
cd ../frontend/acme-chat
npm install
cd ../../cdk

# 3. Deploy CDK stack (creates Cognito, Agent, MCP servers, etc.)
cdk deploy AcmeAgentCoreStack

# 4. Deploy frontend (auto-generates .env from CloudFormation outputs)
cd ../frontend/acme-chat
./scripts/deploy-frontend.sh
```

### Quick Redeploy (After Stack Changes)

If you've already deployed once and just need to update after a `cdk deploy`:

```bash
cd frontend/acme-chat
./scripts/deploy-frontend.sh   # Regenerates .env, rebuilds, and deploys
```

The `deploy-frontend.sh` script automatically:
- Fetches fresh config from CloudFormation outputs
- Generates new `.env` file
- Builds the frontend
- Syncs to S3 and invalidates CloudFront cache

### Create Test User

The deployment does not create users automatically. Create a test user via AWS CLI:

```bash
# Get the User Pool ID from CDK outputs
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name AcmeAgentCoreStack \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' \
  --output text --region us-west-2)

# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username user1@test.com \
  --user-attributes Name=email,Value=user1@test.com Name=email_verified,Value=true \
  --message-action SUPPRESS \
  --region us-west-2

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username user1@test.com \
  --password 'Abcd1234@' \
  --permanent \
  --region us-west-2
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one symbol

Alternatively, create users via the [AWS Cognito Console](https://console.aws.amazon.com/cognito/users).

## Configuration

- **Region**: us-west-2
- **Model**: Claude Haiku 4.5 (via inference profile)
- **Authentication**: AWS Cognito with JWT

## Features

- **Conversation Memory**: Persistent conversation history via AgentCore Memory
- **MCP Integration**: 2 MCP servers for AWS docs and Athena data queries
- **Streaming Responses**: Real-time response streaming
- **Code Interpreter**: Python code execution for data visualization

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
