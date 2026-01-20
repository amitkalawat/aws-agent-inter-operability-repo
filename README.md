# AWS Agent Inter-Operability Repository

This repository demonstrates AWS Bedrock AgentCore with MCP (Model Context Protocol) integration for building intelligent agents that can interact with real-time streaming data.

## Architecture Overview

The project is organized into two main stacks:

### Agent Stack (`agent-stack/`)
Contains the AI agent infrastructure built with AWS Bedrock AgentCore:

- **Frontend**: React TypeScript application with AWS Cognito authentication
- **Backend**: Python Strands agent powered by Claude Haiku 4.5
- **Memory**: AWS Bedrock AgentCore Memory for conversation persistence
- **MCP Integration**: 4 MCP servers (AWS Docs, Data Processing, Rekognition, Nova Canvas)
- **Code Interpreter**: Python execution for data visualization

### Data Stack (`data-stack/`)
Contains the streaming data infrastructure and analytics:

- **MSK Cluster**: Apache Kafka managed service for real-time data streaming
- **Data Generation**: Lambda functions generating synthetic ACME Corp telemetry data
- **Data Lake**: S3-based storage with Glue catalog for analytics
- **Dashboard**: CloudWatch-based telemetry visualization

## AWS Services Used

- **AWS Bedrock AgentCore**: Agent runtime, memory, and MCP server hosting
- **Amazon MSK**: Managed Kafka for streaming
- **AWS Lambda**: Data generation and processing
- **Amazon S3**: Data lake storage and image hosting
- **AWS Glue**: Data catalog and ETL
- **Amazon Athena**: SQL queries on data lake
- **AWS Cognito**: Authentication
- **Amazon CloudFront**: Frontend hosting
- **Amazon Rekognition**: Image analysis
- **Amazon Bedrock**: Nova Canvas image generation

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
│       ├── aws-dataprocessing-mcp-server/
│       ├── amazon-rekognition-mcp-server/
│       └── nova-canvas-mcp-server/
│
└── data-stack/                     # Streaming Data Infrastructure
    ├── ibc2025-data-gen-msk-repo-v2/           # MSK cluster CDK
    ├── ibc2025-data-gen-acme-video-telemetry-synthetic/  # Lambda data generators
    ├── ibc2025-data-gen-acme-video-telemetry-dashboard/  # Dashboard CDK
    └── ibc2025-mcp-data-generation-repo/       # Data processing MCP
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
# Deploy MSK Cluster
cd data-stack/ibc2025-data-gen-msk-repo-v2
npm install
cdk deploy

# Deploy Data Generators
cd ../ibc2025-data-gen-acme-video-telemetry-synthetic
cdk deploy
```

## Features

- **Conversation Memory**: Persistent chat history via AgentCore Memory
- **MCP Integration**: Query AWS docs, run Athena SQL, analyze/generate images
- **Streaming Responses**: Real-time response streaming
- **Code Interpreter**: Python execution for charts and data visualization
- **Image Support**: Generate images (Nova Canvas) and analyze them (Rekognition)

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
