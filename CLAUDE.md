# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AWS Bedrock AgentCore demonstration with MCP (Model Context Protocol) integration. The project showcases an ACME Corp chatbot that can query AWS documentation and analyze streaming telemetry data via natural language.

**Region**: us-west-2 | **Model**: Claude Haiku 4.5

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              USER                                         │
│                                │                                          │
│                                ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    AGENT STACK (agent-stack/)                       │  │
│  │                                                                     │  │
│  │   CloudFront ──▶ Cognito ──▶ Bedrock AgentCore Runtime              │  │
│  │   (React App)    (Auth)      (Claude Haiku 4.5 + Memory)            │  │
│  │                                       │                             │  │
│  │                    ┌──────────────────┼──────────────────┐          │  │
│  │                    │       MCP Servers                   │          │  │
│  │                    │  ┌─────────────┐  ┌──────────────┐  │          │  │
│  │                    │  │ AWS Docs    │  │ Data Process │  │          │  │
│  │                    │  │ MCP Server  │  │ MCP Server   │──┼──────┐   │  │
│  │                    │  └─────────────┘  └──────────────┘  │      │   │  │
│  │                    └─────────────────────────────────────┘      │   │  │
│  └─────────────────────────────────────────────────────────────────┼───┘  │
│                                                                    │      │
│                                                          Athena Queries   │
│                                                                    │      │
│  ┌─────────────────────────────────────────────────────────────────┼───┐  │
│  │                    DATA STACK (data-stack/)                     │   │  │
│  │                                                                 ▼   │  │
│  │   EventBridge ──▶ Lambda ──▶ Kinesis ──▶ Firehose ──▶ S3 Data Lake  │  │
│  │   (5 min)         (Generator)  (Stream)              (Glue + Athena)│  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

## Build & Deploy Commands

### Agent Stack
```bash
cd agent-stack/cdk
npm install

# Deploy CDK stack (Cognito, Agent, MCP servers)
cdk deploy AcmeAgentCoreStack

# Deploy frontend (auto-generates .env from CloudFormation)
cd ../frontend/acme-chat
./scripts/deploy-frontend.sh
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
cd data-stack/consolidated-data-stack
npm install
npm run build
cdk deploy --all
```

### Create Test User (after stack deploy)
```bash
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name AcmeAgentCoreStack \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' --output text --region us-west-2)

aws cognito-idp admin-create-user --user-pool-id $USER_POOL_ID \
  --username user1@test.com --user-attributes Name=email,Value=user1@test.com Name=email_verified,Value=true \
  --message-action SUPPRESS --region us-west-2

aws cognito-idp admin-set-user-password --user-pool-id $USER_POOL_ID \
  --username user1@test.com --password 'Abcd1234@' --permanent --region us-west-2
```

## Key Files

| Path | Purpose |
|------|---------|
| `agent-stack/cdk/lib/acme-stack.ts` | Main CDK stack orchestrating all constructs |
| `agent-stack/cdk/lib/config/index.ts` | Central configuration (region, naming, Cognito, model) |
| `agent-stack/cdk/lib/constructs/secrets-construct.ts` | MCP credentials sync (Custom Resource) |
| `agent-stack/cdk/docker/agent/strands_claude.py` | Main agent logic with MCP client management |
| `agent-stack/frontend/acme-chat/src/services/AuthService.ts` | Cognito auth (USER_PASSWORD_AUTH flow) |
| `agent-stack/frontend/acme-chat/src/services/AgentCoreService.ts` | Agent invocation API client |
| `data-stack/consolidated-data-stack/lib/config.ts` | Data stack configuration |

## MCP Servers

Located in `agent-stack/aws-mcp-server-agentcore/`:
- **aws-documentation-mcp-server**: Search AWS documentation
- **aws-dataprocessing-mcp-server**: Athena SQL queries on ACME telemetry data

## Important Implementation Details

### Authentication
- Frontend uses direct Cognito API with `USER_PASSWORD_AUTH` flow (not Hosted UI)
- MCP servers use OAuth with dedicated Cognito client (`AcmeMcpClientId`)
- MCP credentials synced to Secrets Manager via CDK Custom Resource on every deploy
- Agent caches secrets for 5 minutes (TTL in `secrets_manager.py`)

### MCP Server Invocation
- **Accept Header**: Must include `application/json, text/event-stream` or get 406 error
- **SSE Response**: MCP responses are Server-Sent Events format
- **Session ID**: Capture `mcp-session-id` header from initialize response

### Data Stack
- **Kinesis**: On-Demand mode (auto-scales), 24hr retention
- **Firehose**: Delivers to S3 with Hive partitioning (year/month/day/hour)
- **Generator Lambda**: EventBridge scheduled (5 min), 1000 events per batch

## Logs
```bash
# Agent runtime logs (replace runtime ID with actual)
aws logs tail /aws/bedrock-agentcore/runtimes/acme_chatbot-* --region us-west-2 --since 10m

# Data generator Lambda
aws logs tail /aws/lambda/acme-data-generator --region us-west-2 --since 10m
```

## Athena Schema

**Database**: `acme_telemetry` | **Table**: `streaming_events`

| Column | Type | Values |
|--------|------|--------|
| event_type | STRING | 'start', 'pause', 'resume', 'stop', 'complete' |
| title_type | STRING | 'movie', 'series', 'documentary' |
| device_type | STRING | 'mobile', 'web', 'tv', 'tablet' |

## Stack Recreate Checklist

When deleting and recreating the agent stack:
1. `cdk deploy AcmeAgentCoreStack` - deploys infrastructure + syncs MCP secrets
2. Create test user (Cognito User Pool is new)
3. `./scripts/deploy-frontend.sh` - regenerates .env from CloudFormation outputs

All safeguards are automated - no manual secret sync needed.
