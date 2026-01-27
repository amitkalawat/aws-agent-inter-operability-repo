# Consolidated Data Stack

Single CDK stack combining all ACME telemetry data infrastructure:
- MSK Kafka cluster (real-time streaming)
- Lambda data generators (synthetic telemetry)
- S3 Data Lake with Glue catalog (Athena queries)
- Real-time WebSocket dashboard

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  REAL-TIME STREAMING                                                │
│  EventBridge (5 min) → Generator Lambda → Producer Lambda → MSK     │
│                                                      ↓              │
│                              Consumer Lambda → WebSocket API        │
├─────────────────────────────────────────────────────────────────────┤
│  BATCH DATA LAKE (Athena)                                           │
│  Python Generators → Parquet Files → S3 → Glue Catalog → Athena    │
│                                                                     │
│  Tables: customers, titles, telemetry, campaigns                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- AWS CLI configured with credentials
- Node.js 18+ and npm
- Python 3.9+
- CDK CLI (`npm install -g aws-cdk`)

## Quick Start

### Step 1: Deploy Infrastructure

```bash
# Install dependencies
npm install

# Bootstrap CDK (first time only)
npx cdk bootstrap

# Deploy all stacks (takes ~20 minutes for MSK)
npx cdk deploy --all
```

### Step 2: Setup Data Lake

After CDK deployment completes, run the data lake setup script:

```bash
# Generate synthetic data and upload to S3
./scripts/setup_data_lake.sh
```

This script will:
1. Create a Python virtual environment
2. Install dependencies (pandas, faker, pyarrow)
3. Generate synthetic data (10K customers, 1K titles, 100K events, 50 campaigns)
4. Upload Parquet files to S3
5. Create Glue tables
6. Repair partitions for Athena queries

## Stacks

| Stack | Resources |
|-------|-----------|
| AcmeNetworkStack | VPC, NAT Gateway, Security Groups |
| AcmeMskStack | MSK Kafka cluster (3 brokers), CloudWatch logs |
| AcmeDataLakeStack | S3 bucket, Glue database |
| AcmeDataGenStack | Generator/Producer Lambdas, EventBridge schedule |
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
-- Count records in each table
SELECT 'customers' as tbl, COUNT(*) FROM customers
UNION ALL SELECT 'titles', COUNT(*) FROM titles
UNION ALL SELECT 'telemetry', COUNT(*) FROM telemetry
UNION ALL SELECT 'campaigns', COUNT(*) FROM campaigns;

-- Top genres by watch time
SELECT t.genre, SUM(e.watch_duration_seconds)/3600 as hours_watched
FROM telemetry e
JOIN titles t ON e.title_id = t.title_id
GROUP BY t.genre
ORDER BY hours_watched DESC;

-- Active customers by subscription tier
SELECT subscription_tier, COUNT(*) as customer_count
FROM customers
WHERE is_active = true
GROUP BY subscription_tier;

-- Device type distribution
SELECT device_type, COUNT(*) as sessions
FROM telemetry
GROUP BY device_type
ORDER BY sessions DESC;

-- Daily viewing trends
SELECT date, COUNT(*) as events, SUM(watch_duration_seconds)/3600 as hours
FROM telemetry
GROUP BY date
ORDER BY date;
```

## Data Schema

### customers
Customer demographics, subscriptions, and preferences.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | string | Unique identifier |
| email | string | Email address |
| subscription_tier | string | free_with_ads, basic, standard, premium |
| country | string | Country |
| is_active | boolean | Active subscription |
| preferred_genres | array<string> | Genre preferences |

### titles
Content catalog (movies, series, documentaries).

| Column | Type | Description |
|--------|------|-------------|
| title_id | string | Unique identifier |
| title_name | string | Title name |
| title_type | string | movie, series, documentary |
| genre | string | Primary genre |
| duration_minutes | int | Content duration |

### telemetry
Viewing session events (partitioned by date).

| Column | Type | Description |
|--------|------|-------------|
| event_id | string | Unique event ID |
| customer_id | string | Customer reference |
| title_id | string | Title reference |
| event_type | string | start, pause, resume, stop, complete |
| watch_duration_seconds | int | Time watched |
| device_type | string | tv, mobile, tablet, web |
| quality | string | SD, HD, 4K |

### campaigns
Ad campaign performance metrics.

| Column | Type | Description |
|--------|------|-------------|
| campaign_id | string | Unique identifier |
| advertiser_name | string | Advertiser |
| impressions | bigint | Total impressions |
| clicks | bigint | Total clicks |
| click_through_rate | double | CTR percentage |

## Test Real-Time Pipeline

```bash
# Manually invoke the generator
aws lambda invoke --function-name acme-data-generator --region us-west-2 /dev/stdout

# Connect to WebSocket for real-time events
wscat -c wss://<api-id>.execute-api.us-west-2.amazonaws.com/prod
```

## Destroy

```bash
# Remove all stacks
npx cdk destroy --all

# Clean up generated data (optional)
rm -rf output/ venv/
```

## Configuration

All configuration in `lib/config.ts`:

```typescript
Config.env.region         // AWS region (us-west-2)
Config.prefix             // Resource name prefix (acme-data)
Config.msk.brokerCount    // MSK broker count (3)
Config.msk.kafkaVersion   // Kafka version (3.5.1)
Config.lambda.timeout     // Lambda timeout (300s)
```
