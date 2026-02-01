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

### Step 2: Generate Batch Data for Athena

The streaming pipeline generates data every 5 minutes. For immediate testing, generate batch historical data:

```bash
# Create virtual environment (required on macOS)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install pandas pyarrow click tqdm boto3 faker

# Generate synthetic data (adjust counts as needed)
python data_generation/main.py \
  --customers 1000 \
  --titles 500 \
  --telemetry 100000 \
  --campaigns 50 \
  --output-dir output

# Upload all tables to S3
aws s3 sync output/ s3://acme-telemetry-data-<ACCOUNT>-us-west-2/ --exclude "metadata.json" --region us-west-2

# Repair Glue table to discover new partitions (telemetry only - it's partitioned)
aws athena start-query-execution \
  --query-string "MSCK REPAIR TABLE acme_telemetry.streaming_events" \
  --work-group primary \
  --result-configuration "OutputLocation=s3://acme-telemetry-data-<ACCOUNT>-us-west-2/athena-results/" \
  --region us-west-2
```

**Note**: The batch generator outputs:
- `telemetry/` - Hive partitioned (`year=/month=/day=/hour=`)
- `customers/`, `titles/`, `campaigns/` - Single Parquet files

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

**Database**: `acme_telemetry`

| Table | Description | Partitioned |
|-------|-------------|-------------|
| `streaming_events` | Telemetry events (25 columns) | Yes (year/month/day/hour) |
| `customers` | Customer profiles (21 columns) | No |
| `titles` | Video catalog (26 columns) | No |
| `campaigns` | Ad campaigns (34 columns) | No |

### streaming_events (Key Columns)

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

### customers (Key Columns)

| Column | Type | Description |
|--------|------|-------------|
| customer_id | STRING | Unique customer ID |
| subscription_tier | STRING | free_with_ads, basic, standard, premium |
| country | STRING | Customer country |
| is_active | BOOLEAN | Active subscription |
| lifetime_value | DOUBLE | Customer LTV |

### titles (Key Columns)

| Column | Type | Description |
|--------|------|-------------|
| title_id | STRING | Unique title ID |
| title_name | STRING | Title name |
| title_type | STRING | movie, series, documentary |
| genre | STRING | Content genre |
| popularity_score | DOUBLE | Popularity (0-100) |

### campaigns (Key Columns)

| Column | Type | Description |
|--------|------|-------------|
| campaign_id | STRING | Unique campaign ID |
| advertiser_name | STRING | Advertiser name |
| campaign_type | STRING | brand_awareness, conversion, retention |
| impressions | BIGINT | Total impressions |
| click_through_rate | DOUBLE | CTR |

## Query Examples

### Basic Analytics
```sql
-- Total events
SELECT COUNT(*) as total_events FROM acme_telemetry.streaming_events;

-- Events by type
SELECT event_type, COUNT(*) as count
FROM acme_telemetry.streaming_events
GROUP BY event_type ORDER BY count DESC;

-- Device type distribution
SELECT device_type, COUNT(*) as events,
       AVG(watch_duration_seconds) as avg_watch_duration
FROM acme_telemetry.streaming_events
GROUP BY device_type ORDER BY events DESC;
```

### Quality & Performance
```sql
-- Quality distribution with buffering stats
SELECT quality, COUNT(*) as events,
       AVG(buffering_events) as avg_buffering,
       AVG(bandwidth_mbps) as avg_bandwidth
FROM acme_telemetry.streaming_events
GROUP BY quality ORDER BY events DESC;

-- Error rates by device
SELECT device_type,
       SUM(error_count) as total_errors,
       AVG(error_count) as avg_errors_per_session
FROM acme_telemetry.streaming_events
GROUP BY device_type;
```

### Geographic Analysis
```sql
-- Events by country
SELECT country, COUNT(*) as events
FROM acme_telemetry.streaming_events
GROUP BY country ORDER BY events DESC LIMIT 10;

-- ISP performance
SELECT isp, AVG(bandwidth_mbps) as avg_bandwidth,
       AVG(buffering_events) as avg_buffering
FROM acme_telemetry.streaming_events
GROUP BY isp ORDER BY avg_bandwidth DESC;
```

### Time-Based Analysis
```sql
-- Hourly event distribution
SELECT hour, COUNT(*) as events,
       AVG(completion_percentage) as avg_completion
FROM acme_telemetry.streaming_events
GROUP BY hour ORDER BY hour;

-- Daily summary
SELECT day, COUNT(*) as events,
       COUNT(DISTINCT customer_id) as unique_users,
       AVG(watch_duration_seconds) as avg_watch_secs
FROM acme_telemetry.streaming_events
GROUP BY day ORDER BY day;

-- Single partition query (efficient)
SELECT event_type, COUNT(*) as count
FROM acme_telemetry.streaming_events
WHERE year='2026' AND month='01' AND day='15'
GROUP BY event_type;
```

### Engagement Metrics
```sql
-- Completion rates by event type
SELECT event_type,
       AVG(completion_percentage) as avg_completion,
       AVG(watch_duration_seconds) as avg_duration
FROM acme_telemetry.streaming_events
GROUP BY event_type;

-- Top customers by watch time
SELECT customer_id,
       SUM(watch_duration_seconds) as total_watch_time,
       COUNT(*) as sessions
FROM acme_telemetry.streaming_events
GROUP BY customer_id
ORDER BY total_watch_time DESC LIMIT 10;
```

### Customer Analytics
```sql
-- Customers by subscription tier
SELECT subscription_tier, COUNT(*) as customers,
       AVG(lifetime_value) as avg_ltv
FROM acme_telemetry.customers
GROUP BY subscription_tier ORDER BY customers DESC;

-- Active vs churned customers by country
SELECT country,
       SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active,
       SUM(CASE WHEN NOT is_active THEN 1 ELSE 0 END) as churned
FROM acme_telemetry.customers
GROUP BY country ORDER BY active DESC;
```

### Content Analytics
```sql
-- Titles by genre and type
SELECT genre, title_type, COUNT(*) as titles,
       AVG(popularity_score) as avg_popularity
FROM acme_telemetry.titles
GROUP BY genre, title_type ORDER BY titles DESC;

-- Top rated content
SELECT title_name, genre, viewer_rating, popularity_score
FROM acme_telemetry.titles
ORDER BY viewer_rating DESC LIMIT 10;
```

### Campaign Analytics
```sql
-- Campaign performance by type
SELECT campaign_type, COUNT(*) as campaigns,
       SUM(impressions) as total_impressions,
       AVG(click_through_rate) as avg_ctr
FROM acme_telemetry.campaigns
GROUP BY campaign_type;

-- Top performing campaigns
SELECT campaign_name, advertiser_name, impressions,
       click_through_rate, conversion_rate
FROM acme_telemetry.campaigns
WHERE status = 'completed'
ORDER BY conversions DESC LIMIT 10;
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

## Troubleshooting

### Athena Query Fails with HIVE_CURSOR_ERROR
This usually means schema mismatch between Parquet files and Glue table. Fix by recreating the table:

```sql
DROP TABLE IF EXISTS acme_telemetry.streaming_events;

CREATE EXTERNAL TABLE acme_telemetry.streaming_events (
  event_id STRING, event_type STRING, event_timestamp STRING,
  customer_id STRING, title_id STRING, session_id STRING,
  device_id STRING, title_type STRING, device_type STRING,
  device_os STRING, app_version STRING, quality STRING,
  bandwidth_mbps DOUBLE, buffering_events INT,
  buffering_duration_seconds DOUBLE, error_count INT,
  watch_duration_seconds INT, position_seconds INT,
  completion_percentage DOUBLE, ip_address STRING,
  isp STRING, connection_type STRING, country STRING,
  state STRING, city STRING
)
PARTITIONED BY (year STRING, month STRING, day STRING, hour STRING)
STORED AS PARQUET
LOCATION 's3://acme-telemetry-data-<ACCOUNT>-us-west-2/telemetry/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

MSCK REPAIR TABLE acme_telemetry.streaming_events;
```

### No Data in Athena Queries
1. Check S3 has data: `aws s3 ls s3://acme-telemetry-data-<ACCOUNT>-us-west-2/telemetry/ --recursive`
2. Run partition repair: `MSCK REPAIR TABLE acme_telemetry.streaming_events`
3. Verify partition format matches Glue schema (`year=/month=/day=/hour=`)

### Python Dependency Issues on macOS
Use virtual environment:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pandas pyarrow click tqdm boto3 faker
```

## Destroy

```bash
# Remove all stacks
npx cdk destroy --all

# Kinesis Data Stream may not be deleted by CDK - delete manually if needed
aws kinesis delete-stream --stream-name acme-telemetry-stream --region us-west-2

# Clean up orphaned CloudWatch log groups
for log_group in $(aws logs describe-log-groups --region us-west-2 \
  --query 'logGroups[?contains(logGroupName, `acme`)].logGroupName' --output text); do
  aws logs delete-log-group --log-group-name "$log_group" --region us-west-2
done
```
