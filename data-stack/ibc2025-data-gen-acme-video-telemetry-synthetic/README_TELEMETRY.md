# ACME Video Telemetry Pipeline

## Overview
This repository contains the ACME video streaming telemetry generation and analytics pipeline. It generates realistic streaming telemetry data using real title and customer IDs from the existing `acme_streaming_data` database, enabling proper data correlation for comprehensive analytics.

## Architecture

```
┌─────────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
│   EventBridge       │──────▶│  Generator Lambda   │──────▶│  Producer Lambda    │
│   (5 min schedule)  │       │  (Telemetry Gen)    │       │  (MSK Producer)     │
└─────────────────────┘       └─────────────────────┘       └─────────────────────┘
                                         │                            │
                                         ▼                            ▼
                              ┌─────────────────────┐       ┌─────────────────────┐
                              │  Data Loader Lambda │       │    Amazon MSK       │
                              │  (Reference Data)   │       │    (Kafka Topic)    │
                              └─────────────────────┘       └─────────────────────┘
                                         │                            │
                                         ▼                            ▼
                              ┌─────────────────────┐       ┌─────────────────────┐
                              │  Athena Database    │       │  Kinesis Firehose   │
                              │  (acme_streaming)   │       │  (Buffer & Format)  │
                              └─────────────────────┘       └─────────────────────┘
                                                                      │
                                                                      ▼
                                                            ┌─────────────────────┐
                                                            │    Amazon S3        │
                                                            │  (Data Lake)        │
                                                            └─────────────────────┘
                                                                      │
                                                                      ▼
                                                            ┌─────────────────────┐
                                                            │  AWS Glue Crawler   │
                                                            │  (Hourly Partition) │
                                                            └─────────────────────┘
                                                                      │
                                                                      ▼
                                                            ┌─────────────────────┐
                                                            │    Amazon Athena    │
                                                            │    (Analytics)      │
                                                            └─────────────────────┘
```

## Components

### 1. Lambda Functions

#### Telemetry Generator (`lambda/telemetry_generator`)
- Generates realistic video streaming telemetry events
- Uses real title and customer IDs from reference data
- Implements weighted selection based on popularity scores
- Simulates different viewing patterns (start, stop, pause, resume, complete)

#### MSK Producer (`lambda/msk_producer`)
- Receives telemetry events from Generator
- Publishes events to Amazon MSK (Kafka) topic
- Implements SASL/SSL authentication with IAM
- Auto-creates topics if they don't exist

#### Data Loader (`lambda/data_loader`)
- Fetches real titles and customers from Athena
- Categorizes data by popularity and activity levels
- Caches reference data in S3 for performance
- Provides weighted lists for realistic data distribution

### 2. Infrastructure

#### Amazon MSK
- **Cluster**: `simple-msk-eu-central-1`
- **Topic**: `acme-telemetry`
- **Authentication**: IAM (SASL/SSL)
- **Region**: eu-central-1

#### Kinesis Data Firehose
- **Delivery Stream**: `AcmeTelemetry-MSK-to-S3`
- **Buffer Size**: 5 MB
- **Buffer Interval**: 60 seconds
- **Compression**: GZIP
- **Output Format**: JSON

#### S3 Data Lake
- **Bucket**: `acme-telemetry-241533163649-eu-central-1`
- **Prefix**: `telemetry/`
- **Partitioning**: `year/month/day/hour`

#### AWS Glue
- **Crawler**: `AcmeTelemetry-S3-Crawler`
- **Schedule**: Hourly (cron: `0 * * * ? *`)
- **Database**: `acme_telemetry`
- **Table**: `video_telemetry_json`

## Deployment

### Prerequisites
- AWS CLI configured with appropriate credentials
- Python 3.9+
- Existing MSK cluster in VPC
- Existing `acme_streaming_data` database with `titles` and `customers` tables

### Manual Deployment Steps

1. **Deploy Lambda Functions**:
```bash
cd scripts
./deploy_lambdas.sh
```

2. **Create Kinesis Firehose**:
```bash
aws firehose create-delivery-stream \
  --cli-input-json file://config/firehose-config-frankfurt.json \
  --region eu-central-1
```

3. **Setup EventBridge Schedule**:
```bash
./setup_eventbridge.sh
```

4. **Create Athena Database and Table**:
```bash
aws athena start-query-execution \
  --query-string "CREATE DATABASE IF NOT EXISTS acme_telemetry" \
  --result-configuration "OutputLocation=s3://acme-telemetry-241533163649-eu-central-1/athena-results/" \
  --region eu-central-1
```

5. **Setup Glue Crawler**:
```bash
aws glue create-crawler \
  --name AcmeTelemetry-S3-Crawler \
  --role arn:aws:iam::241533163649:role/AcmeTelemetry-GlueCrawler-Role \
  --database-name acme_telemetry \
  --targets "S3Targets=[{Path=s3://acme-telemetry-241533163649-eu-central-1/telemetry/}]" \
  --region eu-central-1
```

## Testing

### 1. Test Data Generation
```bash
# Generate small batch of test events
aws lambda invoke \
  --function-name AcmeTelemetry-Generator \
  --payload '{"test": true, "batch_size": 100}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/test-output.json \
  --region eu-central-1

# Check output
cat /tmp/test-output.json | jq
```

### 2. Verify Data in S3
```bash
# List recent files
aws s3 ls s3://acme-telemetry-241533163649-eu-central-1/telemetry/ \
  --recursive \
  --region eu-central-1 \
  | tail -10

# Download and inspect a file
aws s3 cp s3://acme-telemetry-241533163649-eu-central-1/telemetry/year=2025/month=08/day=11/hour=18/[filename].gz /tmp/sample.gz \
  --region eu-central-1

gunzip -c /tmp/sample.gz | head -5 | jq
```

## Sample Athena Queries

### 1. Basic Event Count
```sql
-- Total events by event type
SELECT 
    event_type,
    COUNT(*) as event_count
FROM acme_telemetry.video_telemetry_json
WHERE year = 2025 AND month = 8 AND day = 11
GROUP BY event_type
ORDER BY event_count DESC;
```

### 2. Top Viewed Titles with Metadata
```sql
-- Join with titles table to get title names and genres
SELECT 
    vt.title_id,
    t.title_name,
    t.genre,
    t.release_year,
    COUNT(*) as view_count,
    COUNT(DISTINCT vt.customer_id) as unique_viewers
FROM acme_telemetry.video_telemetry_json vt
JOIN acme_streaming_data.titles t ON vt.title_id = t.title_id
WHERE vt.year = 2025 AND vt.month = 8 AND vt.day = 11
GROUP BY vt.title_id, t.title_name, t.genre, t.release_year
ORDER BY view_count DESC
LIMIT 20;
```

### 3. Customer Viewing Behavior
```sql
-- Analyze customer viewing patterns with demographics
SELECT 
    c.subscription_tier,
    c.age_group,
    COUNT(DISTINCT vt.customer_id) as active_customers,
    COUNT(*) as total_events,
    AVG(vt.watch_duration_seconds) as avg_watch_duration
FROM acme_telemetry.video_telemetry_json vt
JOIN acme_streaming_data.customers c ON vt.customer_id = c.customer_id
WHERE vt.year = 2025 AND vt.month = 8 AND vt.day = 11
GROUP BY c.subscription_tier, c.age_group
ORDER BY active_customers DESC;
```

### 4. Streaming Quality Analysis
```sql
-- Quality distribution and buffering issues
SELECT 
    quality,
    device_type,
    COUNT(*) as stream_count,
    AVG(bandwidth_mbps) as avg_bandwidth,
    AVG(buffering_events) as avg_buffering_events,
    AVG(buffering_duration_seconds) as avg_buffer_duration,
    SUM(error_count) as total_errors
FROM acme_telemetry.video_telemetry_json
WHERE year = 2025 AND month = 8 AND day = 11
GROUP BY quality, device_type
ORDER BY stream_count DESC;
```

### 5. Content Performance by Genre
```sql
-- Genre popularity and engagement metrics
SELECT 
    t.genre,
    COUNT(DISTINCT vt.title_id) as unique_titles,
    COUNT(DISTINCT vt.customer_id) as unique_viewers,
    COUNT(*) as total_events,
    AVG(vt.completion_percentage) as avg_completion,
    SUM(CASE WHEN vt.event_type = 'complete' THEN 1 ELSE 0 END) as completions
FROM acme_telemetry.video_telemetry_json vt
JOIN acme_streaming_data.titles t ON vt.title_id = t.title_id
WHERE vt.year = 2025 AND vt.month = 8 AND vt.day = 11
GROUP BY t.genre
ORDER BY total_events DESC;
```

### 6. Geographic Distribution
```sql
-- Viewing patterns by location
SELECT 
    country,
    state,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(*) as total_events,
    AVG(bandwidth_mbps) as avg_bandwidth,
    
    -- Device distribution
    SUM(CASE WHEN device_type = 'mobile' THEN 1 ELSE 0 END) as mobile_views,
    SUM(CASE WHEN device_type = 'tv' THEN 1 ELSE 0 END) as tv_views,
    SUM(CASE WHEN device_type = 'web' THEN 1 ELSE 0 END) as web_views,
    SUM(CASE WHEN device_type = 'tablet' THEN 1 ELSE 0 END) as tablet_views
FROM acme_telemetry.video_telemetry_json
WHERE year = 2025 AND month = 8 AND day = 11
GROUP BY country, state
ORDER BY total_events DESC;
```

### 7. Time Series Analysis
```sql
-- Hourly viewing patterns
SELECT 
    hour,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(*) as total_events,
    SUM(CASE WHEN event_type = 'start' THEN 1 ELSE 0 END) as new_sessions,
    SUM(CASE WHEN event_type = 'complete' THEN 1 ELSE 0 END) as completed_views
FROM acme_telemetry.video_telemetry_json
WHERE year = 2025 AND month = 8 AND day = 11
GROUP BY hour
ORDER BY hour;
```

### 8. Popular Content by Customer Segment
```sql
-- Top titles per subscription tier
WITH ranked_titles AS (
    SELECT 
        c.subscription_tier,
        t.title_name,
        t.genre,
        COUNT(*) as view_count,
        ROW_NUMBER() OVER (PARTITION BY c.subscription_tier ORDER BY COUNT(*) DESC) as rank
    FROM acme_telemetry.video_telemetry_json vt
    JOIN acme_streaming_data.customers c ON vt.customer_id = c.customer_id
    JOIN acme_streaming_data.titles t ON vt.title_id = t.title_id
    WHERE vt.year = 2025 AND vt.month = 8 AND vt.day = 11
    GROUP BY c.subscription_tier, t.title_name, t.genre
)
SELECT 
    subscription_tier,
    title_name,
    genre,
    view_count
FROM ranked_titles
WHERE rank <= 5
ORDER BY subscription_tier, rank;
```

### 9. Engagement Metrics
```sql
-- Calculate engagement scores
SELECT 
    t.title_name,
    t.genre,
    COUNT(DISTINCT vt.customer_id) as unique_viewers,
    AVG(vt.watch_duration_seconds) as avg_watch_time,
    AVG(vt.completion_percentage) as avg_completion,
    
    -- Engagement score calculation
    (COUNT(DISTINCT vt.customer_id) * 0.3 + 
     AVG(vt.completion_percentage) * 0.5 + 
     (100 - AVG(COALESCE(vt.buffering_events, 0))) * 0.2) as engagement_score
     
FROM acme_telemetry.video_telemetry_json vt
JOIN acme_streaming_data.titles t ON vt.title_id = t.title_id
WHERE vt.year = 2025 AND vt.month = 8 AND vt.day = 11
GROUP BY t.title_name, t.genre
HAVING COUNT(*) > 10
ORDER BY engagement_score DESC
LIMIT 20;
```

### 10. Network Performance Analysis
```sql
-- ISP performance comparison
SELECT 
    isp,
    connection_type,
    COUNT(*) as stream_count,
    AVG(bandwidth_mbps) as avg_bandwidth,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY bandwidth_mbps) as median_bandwidth,
    AVG(buffering_events) as avg_buffering,
    SUM(error_count) as total_errors,
    
    -- Quality distribution
    SUM(CASE WHEN quality = '4K' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_4k,
    SUM(CASE WHEN quality = 'HD' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_hd,
    SUM(CASE WHEN quality = 'SD' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_sd
    
FROM acme_telemetry.video_telemetry_json
WHERE year = 2025 AND month = 8 AND day = 11
GROUP BY isp, connection_type
HAVING COUNT(*) > 50
ORDER BY avg_bandwidth DESC;
```

## Monitoring

### CloudWatch Metrics
- Lambda invocations and errors
- MSK cluster metrics
- Firehose delivery success rate
- S3 PUT requests

### Logs
- Lambda logs: `/aws/lambda/AcmeTelemetry-*`
- Firehose logs: `/aws/kinesisfirehose/AcmeTelemetry-MSK-to-S3`

## Troubleshooting

### Common Issues

1. **No data in S3**
   - Check Lambda function logs for errors
   - Verify MSK connectivity and topic exists
   - Check Firehose delivery stream status

2. **Athena queries return no results**
   - Run `MSCK REPAIR TABLE acme_telemetry.video_telemetry_json`
   - Verify partitions are correctly created
   - Check S3 bucket permissions

3. **Random IDs instead of real data**
   - Verify Data Loader Lambda is accessible
   - Check IAM permissions for cross-database queries
   - Ensure reference data tables exist in `acme_streaming_data`

## Cost Optimization

1. **S3 Lifecycle Policies**: Move older data to Glacier
2. **Athena Partitioning**: Always use partition filters in queries
3. **Lambda Reserved Concurrency**: Set appropriate limits
4. **MSK Cluster Sizing**: Monitor and adjust based on throughput

## Security Considerations

1. All data is encrypted in transit (TLS) and at rest (S3 SSE)
2. IAM roles follow least privilege principle
3. VPC endpoints used for private connectivity
4. No hardcoded credentials - all authentication via IAM

## License
Proprietary - ACME Corporation

## Support
For issues or questions, contact the Data Engineering team.