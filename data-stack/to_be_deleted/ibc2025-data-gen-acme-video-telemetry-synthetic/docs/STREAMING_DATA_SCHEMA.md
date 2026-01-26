# ACME Video Telemetry - Streaming Data Schema

## Overview

This document provides a comprehensive description of the streaming data schema used in the ACME video telemetry pipeline. The schema captures detailed information about user viewing behavior, technical performance metrics, and system health indicators for a video streaming platform.

## Schema Version

- **Version**: 1.0.0
- **Last Updated**: August 2025
- **Format**: JSON
- **Encoding**: UTF-8
- **Compression**: GZIP (in transit and at rest)

## Data Flow Architecture

```
User Device → Event Generation → Kafka (MSK) → Firehose → S3 Data Lake
                                      ↓
                              Real-time Analytics
```

## Core Schema Structure

### Message Envelope

Each message in the Kafka stream follows this structure:

```json
{
  "key": "customer_id",           // Partition key
  "value": {                      // Telemetry event payload
    "event_id": "...",
    "customer_id": "...",
    // ... all telemetry fields
  },
  "timestamp": 1754920000000,     // Kafka timestamp (epoch ms)
  "partition": 0,                 // Kafka partition
  "offset": 12345                 // Kafka offset
}
```

## Field Specifications

### 1. Identifiers

| Field | Type | Format | Required | Description |
|-------|------|--------|----------|-------------|
| `event_id` | STRING | `EVENT_[8-char-hex]` | Yes | Unique identifier for each telemetry event |
| `customer_id` | STRING | `CUST_[8-char-hex]` | Yes | Unique customer/account identifier |
| `title_id` | STRING | `TITLE_[8-char-hex]` | Yes | Content identifier |
| `session_id` | STRING | `SESSION_[8-char-hex]` | Yes | Unique streaming session identifier |
| `device_id` | STRING | `DEVICE_[8-char-hex]` | Yes | Unique device identifier |

### 2. Event Information

| Field | Type | Values | Required | Description |
|-------|------|--------|----------|-------------|
| `event_type` | ENUM | `start`, `stop`, `pause`, `resume`, `complete` | Yes | Type of streaming event |
| `event_timestamp` | TIMESTAMP | ISO 8601 | Yes | UTC timestamp of event occurrence |

### 3. Viewing Metrics

| Field | Type | Range | Required | Description |
|-------|------|-------|----------|-------------|
| `watch_duration_seconds` | INTEGER | 0-86400 | Yes | Total seconds watched in session |
| `position_seconds` | INTEGER | 0-86400 | Yes | Current playback position |
| `completion_percentage` | FLOAT | 0.0-100.0 | Yes | Percentage of content watched |

### 4. Device Information

| Field | Type | Values | Required | Description |
|-------|------|--------|----------|-------------|
| `device_type` | ENUM | `mobile`, `web`, `tv`, `tablet` | Yes | Device category |
| `device_os` | STRING | Various | Yes | Operating system |
| `app_version` | STRING | `X.Y.Z` format | Yes | Application version |

### 5. Quality Metrics

| Field | Type | Range/Values | Required | Description |
|-------|------|--------------|----------|-------------|
| `quality` | ENUM | `SD`, `HD`, `4K` | Yes | Video quality level |
| `bandwidth_mbps` | FLOAT | 0.0-1000.0 | Yes | Available bandwidth in Mbps |
| `buffering_events` | INTEGER | 0-1000 | Yes | Number of buffering events |
| `buffering_duration_seconds` | INTEGER | 0-3600 | Yes | Total buffering time |
| `error_count` | INTEGER | 0-100 | Yes | Number of errors encountered |

### 6. Network Information

| Field | Type | Format | Required | Description |
|-------|------|--------|----------|-------------|
| `ip_address` | STRING | IPv4 | Yes | Client IP address |
| `isp` | STRING | Text | Yes | Internet Service Provider |
| `connection_type` | ENUM | `wifi`, `mobile`, `fiber`, `cable`, `dsl`, `satellite` | Yes | Connection type |

### 7. Geographic Information

| Field | Type | Values | Required | Description |
|-------|------|--------|----------|-------------|
| `country` | STRING | Country name | Yes | Viewer's country |
| `state` | STRING | State/Province | No | Viewer's state/province |
| `city` | STRING | City name | Yes | Viewer's city |

## Event Type Definitions

### `start`
- Indicates the beginning of a streaming session
- `watch_duration_seconds` = 0
- `position_seconds` may be > 0 if resuming

### `stop`
- User stops streaming (exits or switches content)
- Contains accumulated viewing metrics
- May indicate incomplete viewing

### `pause`
- User pauses playback
- Preserves current position
- `watch_duration_seconds` frozen at pause point

### `resume`
- User resumes after pause
- `watch_duration_seconds` = 0 (will accumulate)
- `position_seconds` = resume point

### `complete`
- User completes watching content
- `completion_percentage` typically > 90%
- Indicates successful viewing experience

## Data Quality Rules

### Required Field Validation
- All required fields must be present
- No null values in required fields
- Proper format for all identifiers

### Range Validation
- `completion_percentage`: 0.0 ≤ value ≤ 100.0
- `bandwidth_mbps`: 0.0 ≤ value ≤ 1000.0
- `buffering_duration_seconds` ≤ `watch_duration_seconds`
- `position_seconds` ≤ content total duration

### Logical Validation
- If `event_type` = 'start', then `watch_duration_seconds` = 0
- If `buffering_events` = 0, then `buffering_duration_seconds` = 0
- If `quality` = '4K', then `bandwidth_mbps` ≥ 15.0

## Kafka Topic Configuration

### Topic: `acme-telemetry`

```
Partitions: 20
Replication Factor: 3
Retention: 7 days (604800000 ms)
Compression: gzip
Min In-Sync Replicas: 2
```

### Partitioning Strategy
- Key: `customer_id`
- Ensures all events for a customer go to the same partition
- Maintains event ordering per customer

## Data Volume Expectations

### Peak Load
- **Concurrent Viewers**: 15,000-25,000 (prime time)
- **Events per Viewer**: ~12-20 per hour
- **Peak Events/Second**: ~100-150
- **Daily Volume**: ~10-15 million events
- **Storage**: ~5-10 GB/day (compressed)

### Off-Peak Load
- **Concurrent Viewers**: 2,000-5,000 (late night)
- **Events per Viewer**: ~8-15 per hour
- **Events/Second**: ~10-25

## S3 Storage Schema

### Partitioning
```
s3://bucket/telemetry/
  year=2025/
    month=08/
      day=11/
        hour=14/
          *.gz
```

### File Format
- **Type**: JSON Lines (newline-delimited JSON)
- **Compression**: GZIP
- **Naming**: `AcmeTelemetry-MSK-to-S3-{partition}-{timestamp}-{uuid}.gz`

## Schema Evolution

### Versioning Strategy
- Schema version included in documentation
- Backward compatible changes only
- New fields added as optional
- Deprecation notices for field removal

### Change Process
1. Update documentation
2. Deploy producers with new schema
3. Update consumers to handle new fields
4. Monitor for compatibility issues

## Data Privacy Considerations

### PII Fields
- `customer_id`: Pseudonymized identifier
- `ip_address`: May be considered PII in some jurisdictions
- `device_id`: Persistent device identifier

### Compliance Notes
- GDPR: Implement right to erasure for customer data
- CCPA: Provide data export capabilities
- Data retention: 7 days in Kafka, configurable in S3

## Sample Data Record

```json
{
  "event_id": "EVENT_a1b2c3d4",
  "customer_id": "CUST_5e6f7g8h",
  "title_id": "TITLE_9i0j1k2l",
  "session_id": "SESSION_3m4n5o6p",
  "event_type": "start",
  "event_timestamp": "2025-08-11T14:30:45.123Z",
  "watch_duration_seconds": 0,
  "position_seconds": 0,
  "completion_percentage": 0.0,
  "device_type": "mobile",
  "device_id": "DEVICE_7q8r9s0t",
  "device_os": "iOS",
  "app_version": "5.2.1",
  "quality": "HD",
  "bandwidth_mbps": 25.5,
  "buffering_events": 0,
  "buffering_duration_seconds": 0,
  "error_count": 0,
  "ip_address": "192.168.1.100",
  "country": "United States",
  "state": "California",
  "city": "Los Angeles",
  "isp": "Comcast",
  "connection_type": "wifi"
}
```

## Related Documentation

- [TELEMETRY_SCHEMA.md](TELEMETRY_SCHEMA.md) - Basic schema reference
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) - Detailed field dictionary
- [SAMPLE_DATA.md](SAMPLE_DATA.md) - Sample data scenarios
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - System deployment