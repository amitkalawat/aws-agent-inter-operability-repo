# Data Stack

Serverless streaming data infrastructure for generating, processing, and analyzing ACME Corp telemetry data.

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

## Components

| Component | Description |
|-----------|-------------|
| **Kinesis Data Stream** | On-Demand mode, auto-scales, 24hr retention |
| **Kinesis Firehose** | Delivers to S3 with Hive partitioning (year/month/day/hour) |
| **Lambda Functions** | Generator creates 1000 synthetic events per batch |
| **S3 Data Lake** | Parquet with SNAPPY compression, Hive partitioned |
| **Glue Catalog** | Table definitions for Athena queries (4 tables) |

## Deployment

```bash
cd data-stack/consolidated-data-stack
npm install
npm run build
npx cdk deploy --all
```

See [consolidated-data-stack/README.md](./consolidated-data-stack/README.md) for detailed instructions.

## Data Schema

**Database**: `acme_telemetry`

| Table | Description | Records |
|-------|-------------|---------|
| `streaming_events` | Telemetry data (partitioned by year/month/day/hour) | Streaming + batch |
| `customers` | Customer profiles | 1,000 |
| `titles` | Video catalog | 500 |
| `campaigns` | Ad campaigns | 50 |

### streaming_events (Key Columns)

| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Unique event identifier |
| event_timestamp | STRING | ISO 8601 timestamp |
| event_type | STRING | start, pause, resume, stop, complete |
| customer_id | STRING | Customer identifier |
| title_id | STRING | Content identifier |
| title_type | STRING | movie, series, documentary |
| device_type | STRING | mobile, web, tv, tablet |
| quality | STRING | SD, HD, 4K |
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

-- Content engagement
SELECT title_type, AVG(watch_duration_seconds) as avg_duration
FROM acme_telemetry.streaming_events
GROUP BY title_type;
```

## Logs

```bash
# Generator Lambda
aws logs tail /aws/lambda/acme-data-generator --region us-west-2 --since 10m

# Producer Lambda
aws logs tail /aws/lambda/acme-data-producer --region us-west-2 --since 10m
```

## Manual Testing

```bash
# Invoke generator manually
aws lambda invoke --function-name acme-data-generator --region us-west-2 /dev/stdout

# Check Kinesis stream
aws kinesis describe-stream-summary --stream-name acme-telemetry-stream --region us-west-2

# Check S3 data
aws s3 ls s3://acme-telemetry-data-<account>-us-west-2/telemetry/ --recursive | tail -10
```
