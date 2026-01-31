# Consolidated Data Stack

Single CDK deployment combining all ACME telemetry data infrastructure:
- Kinesis Data Stream (real-time streaming)
- Kinesis Firehose (S3 delivery)
- Lambda data generators (synthetic telemetry)
- S3 Data Lake with Glue catalog (Athena queries)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  DATA GENERATION                                                     │
│  EventBridge (5 min) → Generator Lambda → Producer Lambda            │
│                                                │                     │
│                                                ▼                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │   Athena     │◀────│ Glue Catalog │◀────│   Kinesis    │         │
│  │  (Queries)   │     │              │     │   Stream     │         │
│  └──────┬───────┘     └──────────────┘     └──────┬───────┘         │
│         │                                         │                  │
│         │              ┌──────────────┐           │                  │
│         └─────────────▶│  S3 Data     │◀──────────┘                  │
│                        │  Lake        │   (via Firehose)             │
│                        └──────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- AWS CLI configured with credentials
- Node.js 18+ and npm
- CDK CLI (`npm install -g aws-cdk`)

## Quick Start

### Step 1: Deploy Infrastructure

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Bootstrap CDK (first time only)
npx cdk bootstrap

# Deploy all stacks
npx cdk deploy --all
```

### Step 2: (Optional) Load Batch Data

After CDK deployment, optionally run the data lake setup script to generate additional batch data for richer Athena queries:

```bash
# Generate synthetic data and upload to S3
./scripts/setup_data_lake.sh
```

This creates additional tables: `customers`, `titles`, `telemetry`, `campaigns` with synthetic data (10K customers, 1K titles, 100K events, 50 campaigns).

## Stacks

| Stack | Resources |
|-------|-----------|
| `AcmeKinesisStack` | Kinesis Data Stream (On-Demand mode, 24hr retention) |
| `AcmeDataLakeStack` | S3 bucket, Glue database and table |
| `AcmeDataGenStack` | Generator/Producer Lambdas, Firehose delivery, EventBridge schedule |

## Outputs

| Stack | Output | Description |
|-------|--------|-------------|
| `AcmeKinesisStack` | StreamArn | Kinesis Data Stream ARN |
| `AcmeKinesisStack` | StreamName | Kinesis stream name |
| `AcmeDataLakeStack` | DataBucketName | S3 bucket for telemetry |
| `AcmeDataLakeStack` | GlueDatabaseName | Athena database name |

## Data Schema

**Database**: `acme_telemetry` | **Table**: `streaming_events`

| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Unique event identifier |
| event_timestamp | STRING | ISO 8601 timestamp |
| event_type | STRING | 'start', 'pause', 'resume', 'stop', 'complete' |
| customer_id | STRING | Customer identifier |
| title_id | STRING | Content identifier |
| title_type | STRING | 'movie', 'series', 'documentary' |
| device_type | STRING | 'mobile', 'web', 'tv', 'tablet' |
| quality | STRING | Stream quality (SD, HD, 4K) |
| watch_duration_seconds | INT | Watch duration |
| completion_percentage | DOUBLE | Completion percentage |

## Query Examples

```sql
-- Total events
SELECT COUNT(*) FROM acme_telemetry.streaming_events;

-- Events by type
SELECT event_type, COUNT(*) as count
FROM acme_telemetry.streaming_events
GROUP BY event_type
ORDER BY count DESC;

-- Events by date
SELECT SUBSTR(event_timestamp, 1, 10) as date, COUNT(*) as count
FROM acme_telemetry.streaming_events
GROUP BY SUBSTR(event_timestamp, 1, 10)
ORDER BY date DESC;

-- Content engagement by title type
SELECT title_type,
       AVG(watch_duration_seconds) as avg_duration,
       AVG(completion_percentage) as avg_completion
FROM acme_telemetry.streaming_events
GROUP BY title_type;

-- Device type distribution
SELECT device_type, COUNT(*) as sessions
FROM acme_telemetry.streaming_events
GROUP BY device_type
ORDER BY sessions DESC;
```

## Manual Testing

```bash
# Invoke generator manually
aws lambda invoke --function-name acme-data-generator --region us-west-2 /dev/stdout

# Check Kinesis stream
aws kinesis describe-stream-summary --stream-name acme-telemetry-stream --region us-west-2

# Check S3 data
aws s3 ls s3://acme-telemetry-data-<account>-us-west-2/telemetry/ --recursive | tail -10

# Repair Athena partitions (after new data arrives)
aws athena start-query-execution \
  --query-string "MSCK REPAIR TABLE acme_telemetry.streaming_events" \
  --result-configuration "OutputLocation=s3://acme-telemetry-data-<account>-us-west-2/athena-results/" \
  --region us-west-2
```

## Logs

```bash
# Generator Lambda
aws logs tail /aws/lambda/acme-data-generator --region us-west-2 --since 10m

# Producer Lambda
aws logs tail /aws/lambda/acme-data-producer --region us-west-2 --since 10m
```

## Configuration

All configuration in `lib/config.ts`:

```typescript
Config.env.region         // AWS region (us-west-2)
Config.prefix             // Resource name prefix (acme-data)
Config.kinesis.streamName // Kinesis stream name
Config.kinesis.streamMode // ON_DEMAND (auto-scales)
Config.glue.databaseName  // Athena database name
Config.lambda.timeout     // Lambda timeout (60s)
```

## Destroy

```bash
# Remove all stacks
npx cdk destroy --all
```
