# VideoTelemetry Table Schema Documentation

## Overview
The VideoTelemetry table captures detailed streaming telemetry data for the ACME video streaming platform. This schema is designed to track user viewing behavior, quality metrics, and technical performance data.

## Schema Definition

### Table Structure
- **Table Name**: `VideoTelemetry`
- **Purpose**: Capture real-time streaming events and metrics for analytics and monitoring
- **Data Volume**: 2,000-25,000 concurrent viewers generating events every 5 minutes

### Field Definitions

| Field Name | Data Type | Description | Example Value |
|------------|-----------|-------------|---------------|
| `event_id` | STRING | Unique identifier for each telemetry event | `EVENT_a1b2c3d4` |
| `customer_id` | STRING | Unique identifier for the customer/account | `CUST_5e6f7g8h` |
| `title_id` | STRING | Identifier for the content being streamed | `TITLE_9i0j1k2l` |
| `session_id` | STRING | Unique streaming session identifier | `SESSION_3m4n5o6p` |
| `event_type` | STRING | Type of streaming event | `start`, `stop`, `pause`, `resume`, `complete` |
| `event_timestamp` | TIMESTAMP | UTC timestamp when event occurred | `2025-08-11T14:30:45.123Z` |
| `watch_duration_seconds` | INTEGER | Total seconds watched in this session | `1800` |
| `position_seconds` | INTEGER | Current playback position in seconds | `900` |
| `completion_percentage` | FLOAT | Percentage of content watched | `45.5` |
| `device_type` | STRING | Type of device used for streaming | `mobile`, `web`, `tv`, `tablet` |
| `device_id` | STRING | Unique device identifier | `DEVICE_7q8r9s0t` |
| `device_os` | STRING | Operating system of the device | `iOS`, `Android`, `Roku OS`, `Windows` |
| `app_version` | STRING | Version of the streaming application | `5.2.1` |
| `quality` | STRING | Video quality being streamed | `SD`, `HD`, `4K` |
| `bandwidth_mbps` | FLOAT | Available bandwidth in Mbps | `25.5` |
| `buffering_events` | INTEGER | Number of buffering events in session | `2` |
| `buffering_duration_seconds` | INTEGER | Total buffering time in seconds | `15` |
| `error_count` | INTEGER | Number of errors encountered | `0` |
| `ip_address` | STRING | Client IP address | `192.168.1.100` |
| `country` | STRING | Country of the viewer | `United States` |
| `state` | STRING | State/province of the viewer | `California` |
| `city` | STRING | City of the viewer | `Los Angeles` |
| `isp` | STRING | Internet Service Provider | `Comcast` |
| `connection_type` | STRING | Type of internet connection | `wifi`, `mobile`, `fiber`, `cable` |

## Event Types

### Streaming Events
- **start**: User begins streaming content
- **stop**: User stops streaming (exits or switches content)
- **pause**: User pauses playback
- **resume**: User resumes playback after pause
- **complete**: User completes watching the content

## Data Patterns

### Device Distribution
- Mobile: ~35%
- TV: ~30%
- Web: ~25%
- Tablet: ~10%

### Quality Distribution
- HD: ~60%
- SD: ~25%
- 4K: ~15%

### Viewing Patterns by Time
- Late Night (2-6 UTC): 2,000-5,000 viewers
- Morning (6-10 UTC): 5,000-10,000 viewers
- Midday (10-14 UTC): 8,000-15,000 viewers
- Afternoon (14-18 UTC): 10,000-18,000 viewers
- Prime Time (18-22 UTC): 15,000-25,000 viewers
- Evening (22-2 UTC): 8,000-15,000 viewers

## Data Pipeline

### Flow
1. **Generation**: Lambda function generates realistic telemetry events
2. **Production**: Events sent to Amazon MSK (Kafka) topic
3. **Streaming**: Kinesis Data Firehose consumes from MSK
4. **Storage**: Data stored in S3 in compressed Parquet format
5. **Analytics**: Data available for Athena queries and dashboard

### Storage Format
- **Location**: S3 bucket with year/month/day/hour partitioning
- **Format**: GZIP compressed JSON
- **Partitioning**: `year=YYYY/month=MM/day=DD/hour=HH/`
- **Retention**: 7 days in Kafka, indefinite in S3

## Use Cases

### Real-time Analytics
- Monitor concurrent viewers
- Track streaming quality metrics
- Identify buffering issues
- Geographic distribution analysis

### Business Intelligence
- Content popularity analysis
- Device and platform usage
- Peak viewing time identification
- ISP performance comparison

### Technical Monitoring
- Application version adoption
- Error rate tracking
- Bandwidth utilization
- Quality of Service (QoS) metrics

## Sample Query Examples

### Top Content by Viewers
```sql
SELECT 
    title_id,
    COUNT(DISTINCT customer_id) as unique_viewers,
    AVG(completion_percentage) as avg_completion
FROM VideoTelemetry
WHERE event_type = 'complete'
GROUP BY title_id
ORDER BY unique_viewers DESC
LIMIT 10;
```

### Device Type Distribution
```sql
SELECT 
    device_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT customer_id) as unique_users
FROM VideoTelemetry
WHERE date = CURRENT_DATE
GROUP BY device_type;
```

### Buffering Analysis by ISP
```sql
SELECT 
    isp,
    AVG(buffering_events) as avg_buffering,
    AVG(bandwidth_mbps) as avg_bandwidth
FROM VideoTelemetry
WHERE buffering_events > 0
GROUP BY isp
ORDER BY avg_buffering DESC;
```