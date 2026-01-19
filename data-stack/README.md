# Data Stack

This stack contains the streaming data infrastructure for generating, processing, and analyzing ACME Corp telemetry data.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Lambda         │────▶│   Amazon MSK     │────▶│  Kinesis        │
│  (Generator)    │     │   (Kafka)        │     │  Firehose       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  MCP Server     │◀────│  Amazon Athena   │◀────│  S3 Data Lake   │
│  (AgentCore)    │     │  (SQL Queries)   │     │  + Glue Catalog │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Components

### MSK Cluster (`ibc2025-data-gen-msk-repo-v2/`)
Amazon Managed Streaming for Apache Kafka:
- Serverless MSK cluster
- IAM authentication
- Topics: `acme-telemetry`

**Tech Stack**: AWS CDK (TypeScript)

### Data Generators (`ibc2025-data-gen-acme-video-telemetry-synthetic/`)
Lambda functions generating synthetic data:
- **Generator**: Creates telemetry events
- **Producer**: Sends events to MSK
- **DataLoader**: Loads data to S3

**Data Types**:
- Video streaming events (start, pause, resume, stop, complete)
- User engagement metrics
- Content metadata

**Tech Stack**: Python 3.11, AWS Lambda

### Dashboard (`ibc2025-data-gen-acme-video-telemetry-dashboard/`)
CloudWatch-based telemetry visualization:
- Real-time metrics
- Streaming analytics
- Custom dashboards

**Tech Stack**: AWS CDK (TypeScript), React

### MCP Server (`ibc2025-mcp-data-generation-repo/`)
Data Processing MCP server for agent queries:
- Athena SQL query execution
- Schema discovery
- Real-time data access

**Tech Stack**: Python 3.11, AWS Bedrock AgentCore Runtime

## Data Schema

### ACME Telemetry Database

**Table: `streaming_events`**
| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Unique event identifier |
| event_timestamp | VARCHAR | Event time (requires CAST to timestamp) |
| event_type | STRING | 'start', 'pause', 'resume', 'stop', 'complete' |
| user_id | STRING | User identifier |
| content_id | STRING | Content identifier |
| title_type | STRING | 'movie', 'series', 'documentary' |
| device_type | STRING | Device used for streaming |
| quality | STRING | Stream quality |
| duration_seconds | INT | Event duration |

## Deployment

### Deploy MSK Cluster

```bash
cd ibc2025-data-gen-msk-repo-v2
npm install
cdk bootstrap  # First time only
cdk deploy
```

### Deploy Data Generators

```bash
cd ibc2025-data-gen-acme-video-telemetry-synthetic
cd cdk
npm install
cdk deploy
```

### Deploy Dashboard

```bash
cd ibc2025-data-gen-acme-video-telemetry-dashboard/telemetry-dashboard-cdk
npm install
cdk deploy
```

### Deploy MCP Server

```bash
cd ibc2025-mcp-data-generation-repo
source .venv/bin/activate
python deploy_mcp_server.py
```

The MCP server is deployed to AWS Bedrock AgentCore Runtime, not ECS.

## CloudFormation Stacks

| Stack Name | Description |
|------------|-------------|
| `SimpleMskStack-eu-central-1` | MSK Serverless cluster |
| `AcmeStreamingData-Glue` | Glue catalog and crawlers |
| `AcmeStreamingData-DataLake` | S3 buckets and Firehose |
| `TelemetryDashboardStack` | CloudWatch dashboard |

## Query Examples

```sql
-- Recent streaming events
SELECT * FROM acme_telemetry.streaming_events
WHERE CAST(event_timestamp AS timestamp) > current_timestamp - interval '1' hour
LIMIT 100;

-- Events by type
SELECT event_type, COUNT(*) as count
FROM acme_telemetry.streaming_events
GROUP BY event_type;

-- Top content
SELECT content_id, title_type, COUNT(*) as views
FROM acme_telemetry.streaming_events
WHERE event_type = 'start'
GROUP BY content_id, title_type
ORDER BY views DESC
LIMIT 10;
```

## Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/AcmeTelemetry-Generator --region eu-central-1

# MSK Producer logs
aws logs tail /aws/lambda/AcmeTelemetry-Producer --region eu-central-1
```
