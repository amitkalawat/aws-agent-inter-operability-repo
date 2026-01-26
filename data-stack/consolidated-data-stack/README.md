# Consolidated Data Stack

Single CDK stack combining all ACME telemetry data infrastructure:
- MSK Kafka cluster
- Lambda data generators
- Kinesis Firehose to S3
- Glue catalog and Athena
- Real-time WebSocket dashboard

## Architecture

```
NetworkStack (VPC, Security Groups)
       ↓
MskStack (Kafka 3.5.1, 3 brokers)
       ↓
    ┌──┴──┐
    ↓     ↓
DataGenStack              DashboardStack
├─ Generator Lambda       ├─ WebSocket API
├─ Producer Lambda        ├─ Consumer Lambda
└─ Firehose → S3         └─ DynamoDB connections
       ↓
DataLakeStack
├─ S3 (telemetry data)
└─ Glue (acme_telemetry.streaming_events)
```

## Prerequisites

- AWS CLI configured with default profile
- Node.js 18+ and npm
- CDK CLI (`npm install -g aws-cdk`)

## Deploy

```bash
# Install dependencies
npm install

# Bootstrap CDK (first time only)
npx cdk bootstrap

# Deploy all stacks
npx cdk deploy --all
```

## Destroy

```bash
npx cdk destroy --all
```

## Stacks

| Stack | Resources |
|-------|-----------|
| AcmeNetworkStack | VPC, NAT Gateway, Security Groups |
| AcmeMskStack | MSK Kafka cluster (3 brokers), CloudWatch logs |
| AcmeDataLakeStack | S3 bucket, Glue database & table |
| AcmeDataGenStack | Generator/Producer Lambdas, EventBridge, Firehose |
| AcmeDashboardStack | WebSocket API, MSK Consumer Lambda, DynamoDB |

## Outputs

| Stack | Output | Description |
|-------|--------|-------------|
| AcmeNetworkStack | VpcId | VPC for all resources |
| AcmeMskStack | MskClusterArn | Kafka cluster ARN |
| AcmeMskStack | BootstrapServers | Kafka connection string |
| AcmeDataLakeStack | DataBucketName | S3 bucket for telemetry |
| AcmeDataLakeStack | GlueDatabaseName | Athena database |
| AcmeDashboardStack | WebSocketApiEndpoint | Real-time data endpoint |

## Query Data with Athena

```sql
-- Count events by type
SELECT event_type, COUNT(*) as count
FROM acme_telemetry.streaming_events
WHERE year = '2026' AND month = '01'
GROUP BY event_type;

-- Top titles by watch time
SELECT title_id, title_type, SUM(watch_duration_seconds) as total_watch_time
FROM acme_telemetry.streaming_events
WHERE year = '2026'
GROUP BY title_id, title_type
ORDER BY total_watch_time DESC
LIMIT 10;

-- Device distribution
SELECT device_type, COUNT(*) as sessions
FROM acme_telemetry.streaming_events
WHERE event_type = 'start'
GROUP BY device_type;
```

## Configuration

All configuration is centralized in `lib/config.ts`:

```typescript
Config.env.region         // AWS region (us-west-2)
Config.prefix             // Resource name prefix (acme-data)
Config.msk.brokerCount    // MSK broker count (3)
Config.msk.kafkaVersion   // Kafka version (3.5.1)
Config.lambda.timeout     // Lambda timeout (300s)
Config.firehose.bufferInterval // Firehose buffer (60s)
```

## Data Flow

1. **EventBridge** triggers Generator Lambda every 5 minutes
2. **Generator Lambda** creates 1000 synthetic telemetry events
3. **Producer Lambda** publishes events to MSK Kafka topic
4. **Firehose** consumes from MSK and writes to S3 (partitioned by hour)
5. **Glue** catalog enables Athena queries on S3 data
6. **MSK Consumer** broadcasts events to WebSocket clients in real-time
