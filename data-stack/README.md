# Data Stack

Serverless streaming data infrastructure for generating, processing, and analyzing ACME Corp telemetry data.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  EventBridge    │────▶│  Generator       │────▶│  Producer       │
│  (5 min)        │     │  Lambda          │     │  Lambda         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  MCP Server     │◀────│  Amazon Athena   │◀────│  Kinesis Data   │
│  (AgentCore)    │     │  (SQL Queries)   │     │  Stream         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               ▲                         │
                               │                         ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Glue Catalog    │◀────│  Kinesis        │
                        │                  │     │  Firehose → S3  │
                        └──────────────────┘     └─────────────────┘
```

## Stacks

| Stack | Description |
|-------|-------------|
| `AcmeKinesisStack` | Kinesis Data Stream (On-Demand mode, 24hr retention) |
| `AcmeDataLakeStack` | S3 bucket + Glue catalog tables |
| `AcmeDataGenStack` | Generator/Producer Lambdas + Firehose delivery |

## Components

### Kinesis Data Stream
- **Mode**: On-Demand (auto-scales, no shard management)
- **Retention**: 24 hours
- **Encryption**: AWS managed key

### Lambda Functions
- **Generator**: Creates 1000 synthetic telemetry events per batch
- **Producer**: Sends events to Kinesis using `put_records()`

### Firehose Delivery
- **Source**: Kinesis Data Stream (native integration)
- **Destination**: S3 with Hive partitioning (`year=/month=/day=/hour=`)
- **Format**: GZIP compressed JSON

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
| quality | STRING | Stream quality |
| watch_duration_seconds | INT | Watch duration |
| completion_percentage | DOUBLE | Completion percentage |

## Deployment

```bash
cd data-stack/consolidated-data-stack
npm install
npm run build
cdk deploy --all
```

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

-- Content engagement
SELECT title_type, AVG(watch_duration_seconds) as avg_duration,
       AVG(completion_percentage) as avg_completion
FROM acme_telemetry.streaming_events
GROUP BY title_type;
```

## Logs

```bash
# Generator Lambda
aws logs tail /aws/lambda/acme-data-generator --region us-west-2 --since 10m

# Producer Lambda
aws logs tail /aws/lambda/acme-data-producer --region us-west-2 --since 10m

# Firehose delivery
aws logs tail /aws/firehose/acme-data-kinesis-to-s3 --region us-west-2 --since 10m
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
