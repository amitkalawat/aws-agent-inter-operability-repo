# AWS Agent Inter-Operability Repository

This repository demonstrates AWS Bedrock AgentCore with MCP (Model Context Protocol) integration for building intelligent agents that can interact with real-time streaming data.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    USER                                              │
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                         AGENT STACK (agent-stack/)                           │    │
│  │                                                                              │    │
│  │   ┌──────────────┐      ┌─────────────┐      ┌────────────────────────┐     │    │
│  │   │  CloudFront  │      │   Cognito   │      │  Bedrock AgentCore     │     │    │
│  │   │  + S3        │      │  User Pool  │      │  ┌──────────────────┐  │     │    │
│  │   │  (React App) │─────▶│  (Auth)     │─────▶│  │  Main Agent      │  │     │    │
│  │   └──────────────┘      └─────────────┘      │  │  (Claude Haiku)  │  │     │    │
│  │                                              │  │  + Memory        │  │     │    │
│  │                                              │  │  + Code Interp.  │  │     │    │
│  │                                              │  └────────┬─────────┘  │     │    │
│  │                                              └───────────┼────────────┘     │    │
│  │                                                          │                  │    │
│  │                              ┌───────────────────────────┼───────────────┐  │    │
│  │                              │         MCP Servers       │               │  │    │
│  │                              │  ┌──────────────┐  ┌──────▼─────────┐     │  │    │
│  │                              │  │  AWS Docs    │  │ Data Processing│     │  │    │
│  │                              │  │  MCP Server  │  │ MCP Server     │     │  │    │
│  │                              │  └──────────────┘  └───────┬────────┘     │  │    │
│  │                              └────────────────────────────┼──────────────┘  │    │
│  └───────────────────────────────────────────────────────────┼─────────────────┘    │
│                                                              │                      │
│                                                              ▼                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                          DATA STACK (data-stack/)                              │  │
│  │                                                                                │  │
│  │   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                  │  │
│  │   │ EventBridge  │────▶│  Generator   │────▶│  Producer    │                  │  │
│  │   │ (5 min)      │     │  Lambda      │     │  Lambda      │                  │  │
│  │   └──────────────┘     └──────────────┘     └──────┬───────┘                  │  │
│  │                                                    │                          │  │
│  │                                                    ▼                          │  │
│  │   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                  │  │
│  │   │   Athena     │◀────│ Glue Catalog │◀────│   Kinesis    │                  │  │
│  │   │  (Queries)   │     │              │     │   Firehose   │                  │  │
│  │   └──────┬───────┘     └──────────────┘     └──────┬───────┘                  │  │
│  │          │                                         │                          │  │
│  │          │              ┌──────────────┐           │                          │  │
│  │          └─────────────▶│  S3 Data     │◀──────────┘                          │  │
│  │                         │  Lake        │                                      │  │
│  │                         └──────────────┘                                      │  │
│  │                                                                                │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Interaction**: User accesses the React app via CloudFront, authenticates with Cognito
2. **Agent Invocation**: Authenticated requests invoke the Bedrock AgentCore Runtime
3. **MCP Tools**: Agent uses MCP servers to search AWS docs or query telemetry data
4. **Data Queries**: Data Processing MCP server runs Athena SQL queries on the S3 data lake
5. **Data Generation**: EventBridge triggers Lambda functions every 5 minutes to generate synthetic telemetry
6. **Data Pipeline**: Kinesis Firehose delivers streaming data to S3 with Hive partitioning

## Stack Overview

The project is organized into two main stacks:

### Agent Stack (`agent-stack/`)
Contains the AI agent infrastructure built with AWS Bedrock AgentCore:

- **Frontend**: React TypeScript application with AWS Cognito authentication
- **Backend**: Python Strands agent powered by Claude Haiku 4.5
- **Memory**: AWS Bedrock AgentCore Memory for conversation persistence
- **MCP Integration**: 2 MCP servers (AWS Docs, Data Processing)
- **Code Interpreter**: Python execution for data visualization

### Data Stack (`data-stack/`)
Contains the streaming data infrastructure and analytics:

- **Kinesis Data Stream**: On-Demand mode real-time data streaming
- **Kinesis Firehose**: Delivers data to S3 with Hive partitioning
- **Data Generation**: Lambda functions generating synthetic ACME Corp telemetry data
- **Data Lake**: S3-based storage with Glue catalog for Athena queries

## AWS Services Used

- **AWS Bedrock AgentCore**: Agent runtime, memory, and MCP server hosting
- **Amazon Kinesis**: Data Stream and Firehose for streaming
- **AWS Lambda**: Data generation and processing
- **Amazon S3**: Data lake storage
- **AWS Glue**: Data catalog and ETL
- **Amazon Athena**: SQL queries on data lake
- **AWS Cognito**: Authentication
- **Amazon CloudFront**: Frontend hosting

## Region

All resources are deployed in **us-west-2** (Oregon).

## Project Structure

```
aws-agent-inter-operability-repo/
├── agent-stack/                    # AI Agent Infrastructure
│   ├── cdk/                        # CDK infrastructure
│   │   ├── lib/                    # Stack and constructs
│   │   └── docker/agent/           # Agent container code
│   ├── frontend/acme-chat/         # React TypeScript app
│   └── aws-mcp-server-agentcore/   # MCP server implementations
│       ├── aws-documentation-mcp-server/
│       └── aws-dataprocessing-mcp-server/
│
└── data-stack/                     # Streaming Data Infrastructure
    └── consolidated-data-stack/    # Kinesis, Firehose, Glue, Lambdas
```

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js 18+ and npm
- AWS CDK CLI (`npm install -g aws-cdk`)

### Deploy Agent Stack

```bash
cd agent-stack/cdk

# Install dependencies
npm install

# Build frontend
cd ../frontend/acme-chat
npm install
npm run build
cd ../../cdk

# Deploy everything (Cognito, Agent, MCP servers, Frontend)
cdk deploy
```

### Deploy Data Stack

```bash
cd data-stack/consolidated-data-stack
npm install
npm run build
cdk deploy --all
```

## Features

- **Conversation Memory**: Persistent chat history via AgentCore Memory
- **MCP Integration**: Query AWS docs and run Athena SQL queries
- **Streaming Responses**: Real-time response streaming
- **Code Interpreter**: Python execution for charts and data visualization

## Outputs

After deploying the agent stack, you'll get:

| Output | Description |
|--------|-------------|
| `FrontendUrl` | CloudFront URL for the chat application |
| `AgentArn` | Main agent runtime ARN |
| `CognitoUserPoolId` | User pool ID for authentication |
| `CognitoAppClientId` | App client ID for frontend |

## License

MIT
