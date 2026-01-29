# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AWS Bedrock AgentCore demonstration with MCP (Model Context Protocol) integration. The project showcases an ACME Corp chatbot with real-time streaming data, image generation/analysis, and conversation memory.

**Region**: us-west-2 | **Model**: Claude Haiku 4.5

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│   AGENT STACK (agent-stack/)                                │
│   ├─ React Frontend → CloudFront                            │
│   ├─ Bedrock AgentCore Runtime (Python Strands agent)       │
│   ├─ 4 MCP Servers: AWS Docs, Data Processing,              │
│   │                 Rekognition, Nova Canvas                 │
│   ├─ Cognito Authentication                                  │
│   └─ AgentCore Memory                                        │
├─────────────────────────────────────────────────────────────┤
│   MCP REGISTRY STACK (mcpregistry-stack/)                   │
│   ├─ React Frontend → CloudFront                            │
│   ├─ API Gateway + Lambda (Node.js)                         │
│   ├─ DynamoDB (server registry with cached tools)           │
│   └─ Cognito Auth (shared with agent-stack)                 │
├─────────────────────────────────────────────────────────────┤
│   DATA STACK (data-stack/)                                  │
│   ├─ MSK Cluster (Kafka) → Kinesis Firehose → S3            │
│   ├─ Lambda Data Generators (synthetic telemetry)           │
│   ├─ Glue Catalog + Athena for SQL queries                  │
│   └─ CloudWatch Dashboard                                    │
└─────────────────────────────────────────────────────────────┘
```

## Build & Deploy Commands

### Agent Stack (CDK)
```bash
cd agent-stack/cdk
npm install

# Build frontend first
cd ../frontend/acme-chat && npm install && npm run build && cd ../../cdk

# Deploy all (Cognito, Agent, MCP servers, Frontend)
cdk deploy

# Deploy specific construct
cdk deploy AcmeAgentCoreStack
```

### Frontend Development
```bash
cd agent-stack/frontend/acme-chat
npm install
npm start          # Dev server on localhost:3000
npm run build      # Production build
```

### Data Stack
```bash
# Consolidated Data Stack (MSK, Firehose, Glue, Lambdas)
cd data-stack/consolidated-data-stack
npm install && npm run build && cdk deploy --all
```

### MCP Registry Stack
```bash
cd mcpregistry-stack
npm install
cd frontend/mcp-registry && npm install && npm run build && cd ../..
npx cdk deploy
```

**Frontend URL**: Output as `McpRegistryStack.FrontendFrontendUrlE3736ECE`
**Test User**: `testuser@acme.com` / `Testpass1@`

## MSK & Firehose Gotchas

- **MSK Multi-VPC Connectivity**: Use Custom Resource with `updateConnectivity` API (not CfnCluster property)
- **MSK Custom Resource IAM**: Create shared IAM role with all Kafka permissions to avoid race conditions
- **MSK Configuration**: `ServerProperties` as plain string (SDK handles base64 encoding)
- **Firehose MSK Source**: Requires cluster policy allowing `firehose.amazonaws.com` service principal
- **Python Lambda Dependencies**: Use `@aws-cdk/aws-lambda-python-alpha` PythonFunction for proper bundling
- **Kafka IAM Auth**: Token provider must extend `AbstractTokenProvider` from `kafka.sasl.oauth`

## MCP Server Invocation Gotchas

- **MCP Auth Method**: MCP servers use OAuth with specific Cognito client (`AcmeMcpClientId`), not frontend client
- **Client Credentials**: Use `acme-chatbot/mcp-credentials` secret for server-to-server MCP calls
- **Accept Header**: Must include `application/json, text/event-stream` or get 406 error
- **SSE Response**: MCP responses are Server-Sent Events format, parse with `event:` and `data:` lines
- **Session ID**: Capture `mcp-session-id` header from initialize response, pass in subsequent requests
- **TypeScript Lambdas**: Use `NodejsFunction` from `aws-cdk-lib/aws-lambda-nodejs` (not `Code.fromAsset`)

## Logs
```bash
# Agent runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/acme_chatbot-RB6voZDbJ7-DEFAULT --region us-west-2 --since 10m

# MCP server logs (example: Rekognition)
aws logs tail /aws/bedrock-agentcore/runtimes/rekognition_mcp-EFnVxZ5ZKO-DEFAULT --region us-west-2 --since 10m
```

## Key Files

| Path | Purpose |
|------|---------|
| `agent-stack/cdk/lib/acme-stack.ts` | Main CDK stack orchestrating all constructs |
| `agent-stack/cdk/lib/config/index.ts` | Central configuration (region, naming, Cognito, model) |
| `agent-stack/cdk/docker/agent/strands_claude.py` | Main agent logic with MCP client management |
| `agent-stack/cdk/docker/agent/memory_manager.py` | AgentCore Memory integration |
| `agent-stack/frontend/acme-chat/src/config.ts` | Frontend Cognito and AgentCore endpoint config |
| `agent-stack/frontend/acme-chat/src/services/AgentCoreService.ts` | Agent invocation API client |

## MCP Servers

All in `agent-stack/aws-mcp-server-agentcore/`:
- **aws-documentation-mcp-server**: Search AWS documentation
- **aws-dataprocessing-mcp-server**: Athena SQL queries on ACME telemetry data
- **amazon-rekognition-mcp-server**: Image analysis (labels, text, faces, celebrities, moderation)
- **nova-canvas-mcp-server**: AI image generation (deployed to us-east-1 for Nova Canvas availability)

## Data Schema (Athena)

**Database**: `acme_telemetry` | **Table**: `streaming_events`

| Column | Type | Values |
|--------|------|--------|
| event_type | STRING | 'start', 'pause', 'resume', 'stop', 'complete' |
| title_type | STRING | 'movie', 'series', 'documentary' |
| event_timestamp | VARCHAR | Requires `CAST(event_timestamp AS timestamp)` |

## Configuration

Agent and MCP settings in `agent-stack/cdk/lib/config/index.ts`:
- `Config.aws.region`: Deployment region
- `Config.agent.model`: LLM model ID (Claude Haiku 4.5)
- `Config.mcpServers.*`: MCP server names and Docker paths
- `Config.cognito.*`: User pool configuration

Frontend config in `agent-stack/frontend/acme-chat/src/config.ts`:
- `cognito.userPoolId`, `cognito.appClientId`: Auth configuration
- `agentcore.agentArn`: Agent runtime ARN for invocations

## Testing Commands

### Test AgentCore Agent via CLI
```bash
# Get Cognito access token (use access token, NOT id token)
AUTH=$(aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH \
  --client-id <frontend-client-id> --auth-parameters USERNAME=admin@acme.com,PASSWORD=<password> \
  --region us-west-2 --output json)
ACCESS_TOKEN=$(echo "$AUTH" | jq -r '.AuthenticationResult.AccessToken')

# Invoke agent
curl -X POST "https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/<encoded-arn>/invocations?qualifier=DEFAULT" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" -H "Content-Type: application/json" \
  -d '{"prompt": "hello"}'
```

### Test Athena Queries
```bash
# Athena requires explicit S3 output location
S3_BUCKET="s3://acme-telemetry-data-<account>-us-west-2/athena-results/"
aws athena start-query-execution --query-string "SELECT * FROM acme_telemetry.streaming_events LIMIT 10" \
  --result-configuration OutputLocation=$S3_BUCKET --region us-west-2
```

### Additional Batch Tables
- `customers` - subscription_tier, customer demographics (10K rows)
- `titles` - movie/series/documentary catalog (1K rows)
- `telemetry` - device_type usage data (100K rows)
- `campaigns` - advertising campaigns with budgets (50 rows)
