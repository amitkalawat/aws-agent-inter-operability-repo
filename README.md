# AWS Agent Inter-Operability Repository

This repository demonstrates AWS Bedrock AgentCore with MCP (Model Context Protocol) integration for building intelligent agents that can interact with real-time streaming data.

## Architecture Overview

The project is organized into two main stacks:

### Agent Stack (`agent-stack/`)
Contains the AI agent infrastructure built with AWS Bedrock AgentCore:

- **Frontend**: React TypeScript application with AWS Cognito authentication
- **Backend**: Python Strands agent powered by Claude 3.7 Sonnet
- **Memory**: AWS Bedrock AgentCore Memory for conversation persistence
- **MCP Integration**: Dual MCP support for AWS Documentation and Data Processing
- **Tools**: Calculator (SymPy) and Weather utilities

### Data Stack (`data-stack/`)
Contains the streaming data infrastructure and analytics:

- **MSK Cluster**: Apache Kafka managed service for real-time data streaming
- **Data Generation**: Lambda functions generating synthetic ACME Corp telemetry data
- **Data Lake**: S3-based storage with Glue catalog for analytics
- **Dashboard**: CloudWatch-based telemetry visualization
- **MCP Server**: Data processing MCP server for agent queries

## AWS Services Used

- **AWS Bedrock AgentCore**: Agent runtime, memory, and MCP server hosting
- **Amazon MSK**: Managed Kafka for streaming
- **AWS Lambda**: Data generation and processing
- **Amazon S3**: Data lake storage
- **AWS Glue**: Data catalog and ETL
- **Amazon Athena**: SQL queries on data lake
- **AWS Cognito**: Authentication
- **Amazon CloudFront**: Frontend hosting

## Region

All resources are deployed in **eu-central-1** (Frankfurt).

## Project Structure

```
aws-agent-inter-operability-repo/
├── agent-stack/                    # AI Agent Infrastructure
│   ├── frontend/                   # React TypeScript app
│   ├── backend/                    # Python Strands agent
│   │   ├── agent/                  # Agent source code
│   │   └── deployment/             # Deployment scripts
│   ├── infrastructure/             # Cognito setup
│   └── aws-mcp-server-agentcore/   # MCP server implementations
│
└── data-stack/                     # Streaming Data Infrastructure
    ├── ibc2025-data-gen-msk-repo-v2/           # MSK cluster CDK
    ├── ibc2025-data-gen-acme-video-telemetry-synthetic/  # Lambda data generators
    ├── ibc2025-data-gen-acme-video-telemetry-dashboard/  # Dashboard CDK
    └── ibc2025-mcp-data-generation-repo/       # Data processing MCP
```

## Configuration

Before deploying, you need to configure the following files with your own values:

### Agent Stack Configuration

| Template File | Local File (create) | Description |
|---------------|---------------------|-------------|
| `agent-stack/aws-mcp-server-agentcore/.env.template` | `.env.local` | Cognito credentials |
| `agent-stack/backend/deployment/secrets.template.json` | `secrets.local.json` | MCP URLs and Cognito secrets |
| `agent-stack/infrastructure/cognito/cognito_config.json` | `cognito_config.local.json` | Cognito user pool config |

### Data Stack Configuration

| File | Description |
|------|-------------|
| `data-stack/ibc2025-mcp-data-generation-repo/cdk/stacks/analytics_stack.py` | Set Redshift admin password |

### Environment Variables

Set these environment variables before running deployment scripts:

```bash
export COGNITO_ADMIN_PASSWORD="<your-secure-password>"
export AWS_REGION="eu-central-1"
```

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js 18+ and npm
- Python 3.11+
- AWS CDK CLI (`npm install -g aws-cdk`)

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

### Deploy Agent Stack

```bash
# Deploy backend agent
cd agent-stack/backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/memory_manager.py .
cp ../agent/requirements.txt .
source .venv/bin/activate
python deploy_agent_with_auth.py

# Deploy frontend
cd ../../frontend/acme-chat
npm install
npm run build
# Deploy to CloudFront
```

## License

MIT
