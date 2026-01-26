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
# MSK Cluster
cd data-stack/ibc2025-data-gen-msk-repo-v2
npm install && cdk deploy

# Data Generators
cd data-stack/ibc2025-data-gen-acme-video-telemetry-synthetic/cdk
npm install && cdk deploy

# Dashboard
cd data-stack/ibc2025-data-gen-acme-video-telemetry-dashboard/telemetry-dashboard-cdk
npm install && cdk deploy
```

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
