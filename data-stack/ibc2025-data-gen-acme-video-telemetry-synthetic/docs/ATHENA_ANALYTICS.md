# ACME Telemetry - Athena Analytics Guide

## Overview

This guide provides instructions for querying telemetry data using Amazon Athena. The data is stored in S3 in JSON format with GZIP compression and partitioned by year/month/day/hour.

## 📊 Database Setup

### Create Database
```sql
CREATE DATABASE IF NOT EXISTS acme_telemetry
COMMENT 'ACME Video Streaming Telemetry Data';
```

### Create Table
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS acme_telemetry.video_telemetry_json (
    event_id string,
    customer_id string,
    title_id string,
    session_id string,
    event_type string,
    event_timestamp string,
    watch_duration_seconds int,
    position_seconds int,
    completion_percentage double,
    device_type string,
    device_id string,
    device_os string,
    app_version string,
    quality string,
    bandwidth_mbps double,
    buffering_events int,
    buffering_duration_seconds int,
    error_count int,
    ip_address string,
    country string,
    state string,
    city string,
    isp string,
    connection_type string
)
PARTITIONED BY (
    year int,
    month int,
    day int,
    hour int
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES ('ignore.malformed.json' = 'true')
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://acme-telemetry-878687028155-us-west-2/telemetry/'
TBLPROPERTIES ('compressionType'='gzip');
```

### Load Partitions
```sql
MSCK REPAIR TABLE acme_telemetry.video_telemetry_json;
```

## 📈 Sample Query Results

Based on actual data in S3, here are some key insights:

### Event Distribution
- **Complete**: 22.08% (34 events)
- **Stop**: 20.78% (32 events)
- **Resume**: 20.13% (31 events)
- **Pause**: 19.48% (30 events)
- **Start**: 16.88% (26 events)

### Device Usage
- **TV**: 61 events, 50 unique users, 8.88 Mbps avg bandwidth
- **Mobile**: 48 events, 42 unique users, 10.95 Mbps avg bandwidth
- **Tablet**: 27 events, 27 unique users, 6.99 Mbps avg bandwidth
- **Web**: 17 events, 17 unique users, 10.48 Mbps avg bandwidth

### Quality Preferences
- **HD**: 79 streams (51%), 7.55 Mbps avg, 47.71% completion
- **SD**: 45 streams (29%), 3.61 Mbps avg, 47.72% completion
- **4K**: 29 streams (19%), 23.28 Mbps avg, 52.87% completion

## 🔍 Analytics Queries

### 1. Overview Statistics
```sql
SELECT 
    COUNT(*) as total_events,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT title_id) as unique_titles,
    MIN(event_timestamp) as earliest_event,
    MAX(event_timestamp) as latest_event
FROM acme_telemetry.video_telemetry_json;
```

### 2. User Engagement Metrics
```sql
SELECT 
    customer_id,
    COUNT(DISTINCT session_id) as sessions,
    COUNT(DISTINCT title_id) as titles_watched,
    SUM(watch_duration_seconds) / 3600.0 as total_hours_watched,
    AVG(completion_percentage) as avg_completion
FROM acme_telemetry.video_telemetry_json
GROUP BY customer_id
ORDER BY total_hours_watched DESC
LIMIT 20;
```

### 3. Content Performance
```sql
SELECT 
    title_id,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(CASE WHEN event_type = 'start' THEN 1 END) as starts,
    COUNT(CASE WHEN event_type = 'complete' THEN 1 END) as completions,
    ROUND(100.0 * COUNT(CASE WHEN event_type = 'complete' THEN 1 END) / 
          NULLIF(COUNT(CASE WHEN event_type = 'start' THEN 1 END), 0), 2) as completion_rate,
    AVG(watch_duration_seconds) / 60.0 as avg_minutes_watched
FROM acme_telemetry.video_telemetry_json
GROUP BY title_id
HAVING COUNT(CASE WHEN event_type = 'start' THEN 1 END) > 0
ORDER BY unique_viewers DESC;
```

### 4. Quality of Service Analysis
```sql
SELECT 
    quality,
    device_type,
    COUNT(*) as stream_count,
    AVG(bandwidth_mbps) as avg_bandwidth,
    AVG(buffering_events) as avg_buffering,
    AVG(buffering_duration_seconds) as avg_buffer_time,
    AVG(completion_percentage) as avg_completion
FROM acme_telemetry.video_telemetry_json
GROUP BY quality, device_type
ORDER BY quality, stream_count DESC;
```

### 5. Geographic Performance
```sql
SELECT 
    country,
    state,
    city,
    COUNT(DISTINCT customer_id) as unique_users,
    AVG(bandwidth_mbps) as avg_bandwidth,
    AVG(buffering_events) as avg_buffering,
    COUNT(CASE WHEN error_count > 0 THEN 1 END) as sessions_with_errors
FROM acme_telemetry.video_telemetry_json
GROUP BY country, state, city
ORDER BY unique_users DESC;
```

### 6. ISP Performance Comparison
```sql
SELECT 
    isp,
    connection_type,
    COUNT(*) as sessions,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY bandwidth_mbps) as median_bandwidth,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY bandwidth_mbps) as p95_bandwidth,
    AVG(buffering_events) as avg_buffering,
    AVG(error_count) as avg_errors
FROM acme_telemetry.video_telemetry_json
GROUP BY isp, connection_type
HAVING COUNT(*) >= 5
ORDER BY median_bandwidth DESC;
```

### 7. Time-based Analysis
```sql
-- Hourly viewing patterns
SELECT 
    hour,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(CASE WHEN event_type = 'start' THEN 1 END) as new_sessions,
    AVG(watch_duration_seconds) / 60.0 as avg_minutes,
    AVG(bandwidth_mbps) as avg_bandwidth
FROM acme_telemetry.video_telemetry_json
GROUP BY hour
ORDER BY hour;

-- Daily trends
SELECT 
    year, month, day,
    COUNT(DISTINCT customer_id) as daily_users,
    COUNT(*) as daily_events,
    SUM(watch_duration_seconds) / 3600.0 as total_hours
FROM acme_telemetry.video_telemetry_json
GROUP BY year, month, day
ORDER BY year, month, day;
```

### 8. Buffering Impact Analysis
```sql
SELECT 
    CASE 
        WHEN buffering_events = 0 THEN '0 - No Buffering'
        WHEN buffering_events BETWEEN 1 AND 2 THEN '1-2 - Light'
        WHEN buffering_events BETWEEN 3 AND 5 THEN '3-5 - Moderate'
        ELSE '6+ - Heavy'
    END as buffering_category,
    COUNT(*) as sessions,
    AVG(completion_percentage) as avg_completion,
    AVG(watch_duration_seconds) / 60.0 as avg_watch_minutes,
    COUNT(CASE WHEN event_type = 'complete' THEN 1 END) * 100.0 / COUNT(*) as completion_rate
FROM acme_telemetry.video_telemetry_json
WHERE event_type IN ('stop', 'complete')
GROUP BY 
    CASE 
        WHEN buffering_events = 0 THEN '0 - No Buffering'
        WHEN buffering_events BETWEEN 1 AND 2 THEN '1-2 - Light'
        WHEN buffering_events BETWEEN 3 AND 5 THEN '3-5 - Moderate'
        ELSE '6+ - Heavy'
    END
ORDER BY buffering_category;
```

### 9. Device OS Performance
```sql
SELECT 
    device_os,
    COUNT(*) as events,
    COUNT(DISTINCT customer_id) as users,
    AVG(bandwidth_mbps) as avg_bandwidth,
    AVG(completion_percentage) as avg_completion,
    SUM(error_count) as total_errors
FROM acme_telemetry.video_telemetry_json
GROUP BY device_os
ORDER BY events DESC;
```

### 10. Session Analysis
```sql
WITH session_metrics AS (
    SELECT 
        session_id,
        customer_id,
        MIN(event_timestamp) as session_start,
        MAX(event_timestamp) as session_end,
        COUNT(*) as event_count,
        MAX(watch_duration_seconds) as total_watch_time,
        MAX(completion_percentage) as max_completion,
        MAX(buffering_events) as total_buffering,
        MAX(error_count) as total_errors
    FROM acme_telemetry.video_telemetry_json
    GROUP BY session_id, customer_id
)
SELECT 
    CASE 
        WHEN total_watch_time < 300 THEN '< 5 min'
        WHEN total_watch_time < 900 THEN '5-15 min'
        WHEN total_watch_time < 1800 THEN '15-30 min'
        WHEN total_watch_time < 3600 THEN '30-60 min'
        ELSE '> 60 min'
    END as session_duration,
    COUNT(*) as session_count,
    AVG(max_completion) as avg_completion,
    AVG(total_buffering) as avg_buffering
FROM session_metrics
GROUP BY 
    CASE 
        WHEN total_watch_time < 300 THEN '< 5 min'
        WHEN total_watch_time < 900 THEN '5-15 min'
        WHEN total_watch_time < 1800 THEN '15-30 min'
        WHEN total_watch_time < 3600 THEN '30-60 min'
        ELSE '> 60 min'
    END
ORDER BY session_count DESC;
```

## 🚀 Running Queries

### Using AWS CLI
```bash
# Run a query
query_id=$(aws athena start-query-execution \
  --query-string "SELECT * FROM acme_telemetry.video_telemetry_json LIMIT 10" \
  --query-execution-context "Database=acme_telemetry" \
  --result-configuration "OutputLocation=s3://acme-telemetry-878687028155-us-west-2/athena-results/" \
  --region us-west-2 \
  --output json | jq -r '.QueryExecutionId')

# Get results
aws athena get-query-results --query-execution-id "$query_id" --region us-west-2
```

### Using the Script
```bash
# Run all analytics queries
./scripts/athena_queries.sh
```

### Using AWS Console
1. Navigate to Athena in AWS Console
2. Select database: `acme_telemetry`
3. Run queries against `video_telemetry_json` table

## 🎯 Key Performance Indicators (KPIs)

Based on the telemetry data, track these KPIs:

### Engagement KPIs
- **Daily Active Users (DAU)**: Unique customers per day
- **Session Duration**: Average watch time per session
- **Completion Rate**: Percentage of content watched to completion
- **Content Popularity**: Views per title

### Quality KPIs
- **Buffering Rate**: Average buffering events per session
- **Error Rate**: Percentage of sessions with errors
- **Bandwidth Utilization**: Average bandwidth by quality level
- **Stream Quality Distribution**: Percentage of HD/4K streams

### Technical KPIs
- **Device Distribution**: Usage by device type
- **Geographic Coverage**: Users by location
- **ISP Performance**: Quality metrics by ISP
- **Peak Usage Times**: Concurrent users by hour

## 📊 Visualization

Query results can be visualized using:
- **QuickSight**: Connect directly to Athena
- **Tableau**: Use Athena connector
- **Power BI**: Via ODBC driver
- **Custom Dashboards**: Export to CSV/JSON

## 💰 Cost Optimization

### Query Best Practices
1. **Use partitions**: Always filter by year/month/day/hour when possible
2. **Limit data scanned**: Use LIMIT for testing
3. **Project only needed columns**: Don't use SELECT *
4. **Use columnar formats**: Consider converting to Parquet for better performance

### Example Optimized Query
```sql
-- Good: Uses partitions and specific columns
SELECT event_type, COUNT(*)
FROM acme_telemetry.video_telemetry_json
WHERE year = 2025 AND month = 8 AND day = 11
GROUP BY event_type;

-- Bad: Scans all data
SELECT *
FROM acme_telemetry.video_telemetry_json;
```

## 🔧 Troubleshooting

### Common Issues

1. **No results returned**
   - Run `MSCK REPAIR TABLE` to discover partitions
   - Check S3 path and permissions

2. **Query timeout**
   - Reduce data scanned using partitions
   - Increase Athena timeout settings

3. **JSON parsing errors**
   - Check for malformed JSON in S3
   - Use `'ignore.malformed.json' = 'true'` in SerDe properties

## 📚 Additional Resources

- [Athena Best Practices](https://docs.aws.amazon.com/athena/latest/ug/best-practices.html)
- [Athena SQL Reference](https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html)
- [Presto Functions](https://prestodb.io/docs/current/functions.html)