# ACME Video Telemetry - Data Dictionary

## Purpose
This data dictionary provides detailed definitions, business rules, and technical specifications for each field in the ACME video telemetry streaming data schema.

---

## Field Definitions

### EVENT_ID
- **Field Name**: `event_id`
- **Data Type**: STRING
- **Format**: `EVENT_[a-f0-9]{8}`
- **Example**: `EVENT_a1b2c3d4`
- **Nullable**: No
- **Unique**: Yes, globally unique
- **Description**: System-generated unique identifier for each telemetry event
- **Business Purpose**: Enable event tracking, deduplication, and troubleshooting
- **Generation**: UUID v4, truncated to 8 hex characters with EVENT_ prefix
- **Validation Rules**:
  - Must match regex pattern `^EVENT_[a-f0-9]{8}$`
  - Must be unique within the system
  - Cannot be modified after creation

### CUSTOMER_ID
- **Field Name**: `customer_id`
- **Data Type**: STRING
- **Format**: `CUST_[a-f0-9]{8}`
- **Example**: `CUST_5e6f7g8h`
- **Nullable**: No
- **Unique**: No (same customer generates multiple events)
- **Description**: Pseudonymized customer account identifier
- **Business Purpose**: Track viewing behavior per account, calculate customer metrics
- **Generation**: Hashed account ID with CUST_ prefix
- **Validation Rules**:
  - Must match regex pattern `^CUST_[a-f0-9]{8}$`
  - Must correspond to valid account in customer database
- **Privacy Notes**: This is a pseudonymized identifier, not directly PII

### TITLE_ID
- **Field Name**: `title_id`
- **Data Type**: STRING
- **Format**: `TITLE_[a-f0-9]{8}`
- **Example**: `TITLE_9i0j1k2l`
- **Nullable**: No
- **Unique**: No (same content viewed by many)
- **Description**: Identifier for the video content being streamed
- **Business Purpose**: Content popularity analysis, recommendation engine input
- **Generation**: Content catalog ID with TITLE_ prefix
- **Validation Rules**:
  - Must match regex pattern `^TITLE_[a-f0-9]{8}$`
  - Should exist in content catalog
- **Related Systems**: Content Management System (CMS)

### SESSION_ID
- **Field Name**: `session_id`
- **Data Type**: STRING
- **Format**: `SESSION_[a-f0-9]{8}`
- **Example**: `SESSION_3m4n5o6p`
- **Nullable**: No
- **Unique**: Yes, per streaming session
- **Description**: Unique identifier for a continuous viewing session
- **Business Purpose**: Group events within same viewing session, calculate session metrics
- **Generation**: Generated at session start, persists until session end
- **Validation Rules**:
  - Must match regex pattern `^SESSION_[a-f0-9]{8}$`
  - All events in a session must have same session_id
- **Lifecycle**: Created on 'start' event, terminated on 'stop' or 'complete'

### EVENT_TYPE
- **Field Name**: `event_type`
- **Data Type**: ENUM/STRING
- **Valid Values**: `start`, `stop`, `pause`, `resume`, `complete`
- **Example**: `start`
- **Nullable**: No
- **Description**: Type of streaming event
- **Business Purpose**: Track user behavior patterns, calculate engagement metrics
- **Validation Rules**:
  - Must be one of the valid values
  - Logical sequence must be maintained (e.g., can't 'resume' without prior 'pause')
- **State Transitions**:
  ```
  start → pause → resume → stop/complete
  start → stop/complete
  ```

### EVENT_TIMESTAMP
- **Field Name**: `event_timestamp`
- **Data Type**: TIMESTAMP
- **Format**: ISO 8601 with timezone
- **Example**: `2025-08-11T14:30:45.123Z`
- **Nullable**: No
- **Timezone**: UTC
- **Description**: Exact time when the event occurred
- **Business Purpose**: Time-series analysis, calculate viewing patterns by time of day
- **Generation**: System timestamp at event creation
- **Validation Rules**:
  - Must be valid ISO 8601 format
  - Must be in UTC (Z suffix)
  - Cannot be future timestamp
  - Should be within reasonable range (not > 24 hours old)

### WATCH_DURATION_SECONDS
- **Field Name**: `watch_duration_seconds`
- **Data Type**: INTEGER
- **Range**: 0 - 86400 (24 hours)
- **Example**: `1800` (30 minutes)
- **Nullable**: No
- **Unit**: Seconds
- **Description**: Total time spent watching in this session
- **Business Purpose**: Calculate engagement, average viewing time, content effectiveness
- **Calculation**: Accumulated time excluding pauses
- **Validation Rules**:
  - Must be >= 0
  - Must be <= 86400 (24 hours)
  - If event_type='start', must be 0
  - Cannot exceed content duration

### POSITION_SECONDS
- **Field Name**: `position_seconds`
- **Data Type**: INTEGER
- **Range**: 0 - 86400
- **Example**: `900` (15 minutes into content)
- **Nullable**: No
- **Unit**: Seconds
- **Description**: Current playback position in the content
- **Business Purpose**: Identify drop-off points, popular segments, skip patterns
- **Validation Rules**:
  - Must be >= 0
  - Must be <= content total duration
  - Should be consistent with watch_duration_seconds

### COMPLETION_PERCENTAGE
- **Field Name**: `completion_percentage`
- **Data Type**: FLOAT
- **Range**: 0.0 - 100.0
- **Example**: `45.5`
- **Nullable**: No
- **Unit**: Percentage
- **Precision**: 2 decimal places
- **Description**: Percentage of content viewed
- **Business Purpose**: Measure content completion rates, identify engaging content
- **Calculation**: `(position_seconds / total_content_duration) * 100`
- **Validation Rules**:
  - Must be between 0.0 and 100.0
  - Should align with position_seconds and content duration

### DEVICE_TYPE
- **Field Name**: `device_type`
- **Data Type**: ENUM/STRING
- **Valid Values**: `mobile`, `web`, `tv`, `tablet`
- **Example**: `mobile`
- **Nullable**: No
- **Description**: Category of device used for streaming
- **Business Purpose**: Device-specific optimization, platform analytics
- **Validation Rules**:
  - Must be one of the valid values
  - Should be consistent within a session

### DEVICE_ID
- **Field Name**: `device_id`
- **Data Type**: STRING
- **Format**: `DEVICE_[a-f0-9]{8}`
- **Example**: `DEVICE_7q8r9s0t`
- **Nullable**: No
- **Unique**: Per physical device
- **Description**: Persistent device identifier
- **Business Purpose**: Track device-specific issues, multi-device usage patterns
- **Generation**: Hashed device hardware ID
- **Privacy Notes**: Persistent identifier, subject to privacy regulations
- **Validation Rules**:
  - Must match regex pattern `^DEVICE_[a-f0-9]{8}$`
  - Should be consistent for same device across sessions

### DEVICE_OS
- **Field Name**: `device_os`
- **Data Type**: STRING
- **Valid Values**: `iOS`, `Android`, `Windows`, `macOS`, `Linux`, `ChromeOS`, `Roku OS`, `Fire TV`, `Apple TV`, `Android TV`, `Smart TV OS`
- **Example**: `iOS`
- **Nullable**: No
- **Description**: Operating system of the streaming device
- **Business Purpose**: OS-specific optimization, compatibility tracking
- **Validation Rules**:
  - Should be consistent with device_type
  - Mobile: iOS, Android
  - Web: Windows, macOS, Linux, ChromeOS
  - TV: Roku OS, Fire TV, Apple TV, Android TV, Smart TV OS
  - Tablet: iOS, Android

### APP_VERSION
- **Field Name**: `app_version`
- **Data Type**: STRING
- **Format**: Semantic versioning `X.Y.Z`
- **Example**: `5.2.1`
- **Nullable**: No
- **Description**: Version of the streaming application
- **Business Purpose**: Version-specific bug tracking, feature adoption analysis
- **Validation Rules**:
  - Must match pattern `^\d+\.\d+\.\d+$`
  - Major.Minor.Patch format

### QUALITY
- **Field Name**: `quality`
- **Data Type**: ENUM/STRING
- **Valid Values**: `SD`, `HD`, `4K`
- **Example**: `HD`
- **Nullable**: No
- **Description**: Video quality level being streamed
- **Business Purpose**: Quality preference analysis, bandwidth optimization
- **Quality Definitions**:
  - SD: Standard Definition (480p)
  - HD: High Definition (720p/1080p)
  - 4K: Ultra High Definition (2160p)
- **Validation Rules**:
  - Must be one of the valid values
  - Should align with bandwidth_mbps capabilities

### BANDWIDTH_MBPS
- **Field Name**: `bandwidth_mbps`
- **Data Type**: FLOAT
- **Range**: 0.0 - 1000.0
- **Example**: `25.5`
- **Nullable**: No
- **Unit**: Megabits per second
- **Precision**: 2 decimal places
- **Description**: Available network bandwidth
- **Business Purpose**: Network performance analysis, quality recommendation
- **Expected Ranges**:
  - SD: 1.5 - 5 Mbps
  - HD: 5 - 15 Mbps
  - 4K: 15 - 30+ Mbps
- **Validation Rules**:
  - Must be > 0
  - Should be reasonable for quality level

### BUFFERING_EVENTS
- **Field Name**: `buffering_events`
- **Data Type**: INTEGER
- **Range**: 0 - 1000
- **Example**: `2`
- **Nullable**: No
- **Description**: Count of buffering occurrences during session
- **Business Purpose**: Quality of experience metrics, network issue detection
- **Validation Rules**:
  - Must be >= 0
  - If 0, buffering_duration_seconds must be 0

### BUFFERING_DURATION_SECONDS
- **Field Name**: `buffering_duration_seconds`
- **Data Type**: INTEGER
- **Range**: 0 - 3600
- **Example**: `15`
- **Nullable**: No
- **Unit**: Seconds
- **Description**: Total time spent buffering
- **Business Purpose**: Calculate rebuffering ratio, QoE scoring
- **Validation Rules**:
  - Must be >= 0
  - Must be 0 if buffering_events = 0
  - Cannot exceed watch_duration_seconds

### ERROR_COUNT
- **Field Name**: `error_count`
- **Data Type**: INTEGER
- **Range**: 0 - 100
- **Example**: `0`
- **Nullable**: No
- **Description**: Number of errors encountered during streaming
- **Business Purpose**: System health monitoring, error rate tracking
- **Error Types**: Network errors, codec errors, DRM errors, etc.
- **Validation Rules**:
  - Must be >= 0
  - High values (>10) indicate serious issues

### IP_ADDRESS
- **Field Name**: `ip_address`
- **Data Type**: STRING
- **Format**: IPv4 (XXX.XXX.XXX.XXX)
- **Example**: `192.168.1.100`
- **Nullable**: No
- **Description**: Client IP address
- **Business Purpose**: Geographic analysis, fraud detection, CDN optimization
- **Privacy Notes**: May be considered PII, handle according to privacy policy
- **Validation Rules**:
  - Must be valid IPv4 format
  - Should not be private range in production

### COUNTRY
- **Field Name**: `country`
- **Data Type**: STRING
- **Valid Values**: ISO country names
- **Example**: `United States`
- **Nullable**: No
- **Description**: Country of the viewer
- **Business Purpose**: Geographic content licensing, regional analytics
- **Source**: GeoIP lookup from ip_address
- **Validation Rules**:
  - Must be valid country name
  - Should match IP geolocation

### STATE
- **Field Name**: `state`
- **Data Type**: STRING
- **Example**: `California`
- **Nullable**: Yes (not all countries have states)
- **Description**: State or province of the viewer
- **Business Purpose**: Regional content preferences, local analytics
- **Source**: GeoIP lookup from ip_address
- **Validation Rules**:
  - Can be empty for countries without states
  - Should be valid state/province for the country

### CITY
- **Field Name**: `city`
- **Data Type**: STRING
- **Example**: `Los Angeles`
- **Nullable**: No
- **Description**: City of the viewer
- **Business Purpose**: Local content recommendations, urban/rural analysis
- **Source**: GeoIP lookup from ip_address
- **Validation Rules**:
  - Must be non-empty
  - Should be valid city name

### ISP
- **Field Name**: `isp`
- **Data Type**: STRING
- **Example**: `Comcast`
- **Nullable**: No
- **Description**: Internet Service Provider name
- **Business Purpose**: ISP performance analysis, peering optimization
- **Common Values**: `Comcast`, `AT&T`, `Verizon`, `Spectrum`, `Cox`, `Frontier`, `CenturyLink`
- **Source**: IP ASN lookup
- **Validation Rules**:
  - Must be non-empty
  - Should be recognized ISP name

### CONNECTION_TYPE
- **Field Name**: `connection_type`
- **Data Type**: ENUM/STRING
- **Valid Values**: `wifi`, `mobile`, `fiber`, `cable`, `dsl`, `satellite`
- **Example**: `wifi`
- **Nullable**: No
- **Description**: Type of internet connection
- **Business Purpose**: Performance expectations, quality recommendations
- **Expected Performance**:
  - fiber: Highest bandwidth, lowest latency
  - cable: High bandwidth, low latency
  - wifi: Variable based on underlying connection
  - dsl: Medium bandwidth, medium latency
  - mobile: Variable bandwidth, variable latency
  - satellite: Lower bandwidth, high latency
- **Validation Rules**:
  - Must be one of the valid values

---

## Data Governance

### Data Classification
- **Confidential**: customer_id, ip_address, device_id
- **Internal**: All other fields
- **Public**: None

### Retention Policy
- **Kafka**: 7 days
- **S3 Raw**: 90 days
- **S3 Aggregated**: 2 years
- **Archived**: 7 years (compressed, cold storage)

### Access Control
- **Read Access**: Data analysts, engineers, product managers
- **Write Access**: Streaming pipeline services only
- **Admin Access**: Data platform team

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-08-11 | Initial version | Data Engineering Team |

---

## Contact

For questions about this data dictionary:
- **Team**: Data Engineering
- **Email**: data-engineering@acme.com
- **Slack**: #data-platform