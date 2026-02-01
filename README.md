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
- Docker (for building container images)
- AWS CDK CLI (`npm install -g aws-cdk`)

### Full Deployment (Both Stacks)

Deploy both stacks in order - data stack first (agent queries its Athena data):

```bash
# 1. Deploy Data Stack (Kinesis, Firehose, S3, Glue, Athena)
cd data-stack/consolidated-data-stack
npm install && npm run build && cdk deploy --all --require-approval never

# 2. Build Frontend FIRST (required before CDK deploy)
cd ../../agent-stack/frontend/acme-chat
npm install && npm run build

# 3. Deploy Agent Stack (Cognito, Agent, MCP servers)
cd ../../cdk
npm install && cdk deploy AcmeAgentCoreStack --require-approval never

# 4. Deploy Frontend with correct config from CloudFormation
cd ../frontend/acme-chat
./scripts/deploy-frontend.sh

# 5. Create test user
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name AcmeAgentCoreStack \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' --output text --region us-west-2)

aws cognito-idp admin-create-user --user-pool-id $USER_POOL_ID \
  --username user1@test.com --user-attributes Name=email,Value=user1@test.com Name=email_verified,Value=true \
  --message-action SUPPRESS --region us-west-2

aws cognito-idp admin-set-user-password --user-pool-id $USER_POOL_ID \
  --username user1@test.com --password 'Abcd1234@' --permanent --region us-west-2
```

> **Important**: The frontend must be built before `cdk deploy` because the CDK stack references the `build/` directory for S3 deployment.

### Generate Batch Data (Optional but Recommended)

The streaming pipeline generates data every 5 minutes. For immediate testing with substantial data:

```bash
cd data-stack/consolidated-data-stack

# Setup Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install pandas pyarrow click tqdm boto3 faker

# Generate all data (customers, titles, campaigns, telemetry)
python data_generation/main.py --customers 1000 --titles 500 --telemetry 100000 --campaigns 50

# Get your account ID
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Upload all tables to S3
aws s3 sync output/ s3://acme-telemetry-data-${ACCOUNT}-us-west-2/ --exclude "metadata.json"

# Repair Athena partitions (telemetry only - it's partitioned)
aws athena start-query-execution \
  --query-string "MSCK REPAIR TABLE acme_telemetry.streaming_events" \
  --work-group primary \
  --result-configuration "OutputLocation=s3://acme-telemetry-data-${ACCOUNT}-us-west-2/athena-results/" \
  --region us-west-2
```

This creates 4 Athena tables: `streaming_events`, `customers`, `titles`, `campaigns`.

### Test Credentials

After deployment, access the CloudFront URL and login with:
- **Email**: `user1@test.com`
- **Password**: `Abcd1234@`

## Features

- **Conversation Memory**: Persistent chat history via AgentCore Memory
- **MCP Integration**: Query AWS docs and run Athena SQL queries
- **Streaming Responses**: Real-time response streaming
- **Code Interpreter**: Python execution for charts and data visualization

## Sample Agent Queries

Once deployed with data, try these natural language queries:

### Telemetry Analytics
- "How many streaming events do we have?"
- "Show me events by device type"
- "What's the quality distribution of streams?"
- "Which countries have the most viewers?"
- "What's the average watch duration by device?"
- "Show hourly viewing patterns"
- "Which ISPs have the best streaming quality?"

### Customer Analytics
- "How many customers do we have by subscription tier?"
- "What's the average lifetime value by country?"
- "Show me the churn rate by subscription tier"

### Content Analytics
- "What are our top rated titles?"
- "Show me the genre distribution of our catalog"
- "Which content types have the highest popularity?"

### Campaign Analytics
- "How are our ad campaigns performing?"
- "What's the average CTR by campaign type?"
- "Show top campaigns by conversions"

### AWS Documentation
- "How do I create an S3 bucket with versioning?"
- "Explain Kinesis Data Streams vs Firehose"
- "What are the best practices for Lambda functions?"

### Data Visualization (Code Interpreter)
- "Create a bar chart of events by device type"
- "Plot the hourly distribution of streaming events"

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
