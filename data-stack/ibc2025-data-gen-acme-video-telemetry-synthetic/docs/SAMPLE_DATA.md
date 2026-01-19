# ACME Video Telemetry - Sample Data Examples

## Overview
This document provides realistic sample data examples for various streaming scenarios. These examples demonstrate the expected data patterns and help validate data processing implementations.

---

## Scenario 1: Complete Viewing Session

**Description**: User watches a 2-hour movie from start to finish on a smart TV with good connection.

### Event 1: Start
```json
{
  "event_id": "EVENT_a1b2c3d4",
  "customer_id": "CUST_5e6f7g8h",
  "title_id": "TITLE_movie001",
  "session_id": "SESSION_xyz12345",
  "event_type": "start",
  "event_timestamp": "2025-08-11T20:00:00.000Z",
  "watch_duration_seconds": 0,
  "position_seconds": 0,
  "completion_percentage": 0.0,
  "device_type": "tv",
  "device_id": "DEVICE_tv567890",
  "device_os": "Roku OS",
  "app_version": "5.2.1",
  "quality": "4K",
  "bandwidth_mbps": 45.2,
  "buffering_events": 0,
  "buffering_duration_seconds": 0,
  "error_count": 0,
  "ip_address": "73.162.241.89",
  "country": "United States",
  "state": "California",
  "city": "San Francisco",
  "isp": "Comcast",
  "connection_type": "fiber"
}
```

### Event 2: Complete
```json
{
  "event_id": "EVENT_b2c3d4e5",
  "customer_id": "CUST_5e6f7g8h",
  "title_id": "TITLE_movie001",
  "session_id": "SESSION_xyz12345",
  "event_type": "complete",
  "event_timestamp": "2025-08-11T22:05:30.000Z",
  "watch_duration_seconds": 7530,
  "position_seconds": 7200,
  "completion_percentage": 100.0,
  "device_type": "tv",
  "device_id": "DEVICE_tv567890",
  "device_os": "Roku OS",
  "app_version": "5.2.1",
  "quality": "4K",
  "bandwidth_mbps": 43.8,
  "buffering_events": 1,
  "buffering_duration_seconds": 3,
  "error_count": 0,
  "ip_address": "73.162.241.89",
  "country": "United States",
  "state": "California",
  "city": "San Francisco",
  "isp": "Comcast",
  "connection_type": "fiber"
}
```

---

## Scenario 2: Mobile Viewing with Interruptions

**Description**: User watches a TV show episode on mobile during commute, with multiple pauses.

### Event 1: Start
```json
{
  "event_id": "EVENT_m1n2o3p4",
  "customer_id": "CUST_abc123de",
  "title_id": "TITLE_show_s01e05",
  "session_id": "SESSION_mob78901",
  "event_type": "start",
  "event_timestamp": "2025-08-11T07:30:00.000Z",
  "watch_duration_seconds": 0,
  "position_seconds": 0,
  "completion_percentage": 0.0,
  "device_type": "mobile",
  "device_id": "DEVICE_iph34567",
  "device_os": "iOS",
  "app_version": "5.1.9",
  "quality": "HD",
  "bandwidth_mbps": 12.5,
  "buffering_events": 0,
  "buffering_duration_seconds": 0,
  "error_count": 0,
  "ip_address": "172.58.12.45",
  "country": "United States",
  "state": "New York",
  "city": "New York",
  "isp": "Verizon",
  "connection_type": "mobile"
}
```

### Event 2: Pause
```json
{
  "event_id": "EVENT_m2n3o4p5",
  "customer_id": "CUST_abc123de",
  "title_id": "TITLE_show_s01e05",
  "session_id": "SESSION_mob78901",
  "event_type": "pause",
  "event_timestamp": "2025-08-11T07:35:15.000Z",
  "watch_duration_seconds": 315,
  "position_seconds": 315,
  "completion_percentage": 12.5,
  "device_type": "mobile",
  "device_id": "DEVICE_iph34567",
  "device_os": "iOS",
  "app_version": "5.1.9",
  "quality": "HD",
  "bandwidth_mbps": 10.2,
  "buffering_events": 2,
  "buffering_duration_seconds": 8,
  "error_count": 0,
  "ip_address": "172.58.12.45",
  "country": "United States",
  "state": "New York",
  "city": "New York",
  "isp": "Verizon",
  "connection_type": "mobile"
}
```

### Event 3: Resume
```json
{
  "event_id": "EVENT_m3n4o5p6",
  "customer_id": "CUST_abc123de",
  "title_id": "TITLE_show_s01e05",
  "session_id": "SESSION_mob78901",
  "event_type": "resume",
  "event_timestamp": "2025-08-11T07:40:00.000Z",
  "watch_duration_seconds": 0,
  "position_seconds": 315,
  "completion_percentage": 12.5,
  "device_type": "mobile",
  "device_id": "DEVICE_iph34567",
  "device_os": "iOS",
  "app_version": "5.1.9",
  "quality": "SD",
  "bandwidth_mbps": 4.5,
  "buffering_events": 0,
  "buffering_duration_seconds": 0,
  "error_count": 0,
  "ip_address": "172.58.14.78",
  "country": "United States",
  "state": "New York",
  "city": "New York",
  "isp": "Verizon",
  "connection_type": "mobile"
}
```

### Event 4: Stop
```json
{
  "event_id": "EVENT_m4n5o6p7",
  "customer_id": "CUST_abc123de",
  "title_id": "TITLE_show_s01e05",
  "session_id": "SESSION_mob78901",
  "event_type": "stop",
  "event_timestamp": "2025-08-11T07:55:30.000Z",
  "watch_duration_seconds": 1245,
  "position_seconds": 1245,
  "completion_percentage": 49.8,
  "device_type": "mobile",
  "device_id": "DEVICE_iph34567",
  "device_os": "iOS",
  "app_version": "5.1.9",
  "quality": "SD",
  "bandwidth_mbps": 3.8,
  "buffering_events": 5,
  "buffering_duration_seconds": 22,
  "error_count": 1,
  "ip_address": "172.58.16.92",
  "country": "United States",
  "state": "New York",
  "city": "New York",
  "isp": "Verizon",
  "connection_type": "mobile"
}
```

---

## Scenario 3: Poor Network Conditions

**Description**: User experiences significant buffering due to poor satellite internet connection.

```json
{
  "event_id": "EVENT_buf12345",
  "customer_id": "CUST_rural789",
  "title_id": "TITLE_docu_nat",
  "session_id": "SESSION_sat45678",
  "event_type": "stop",
  "event_timestamp": "2025-08-11T15:30:00.000Z",
  "watch_duration_seconds": 1800,
  "position_seconds": 900,
  "completion_percentage": 25.0,
  "device_type": "web",
  "device_id": "DEVICE_pc789012",
  "device_os": "Windows",
  "app_version": "5.2.0",
  "quality": "SD",
  "bandwidth_mbps": 1.8,
  "buffering_events": 15,
  "buffering_duration_seconds": 180,
  "error_count": 3,
  "ip_address": "98.45.67.123",
  "country": "United States",
  "state": "Montana",
  "city": "Billings",
  "isp": "Hughes Network",
  "connection_type": "satellite"
}
```

---

## Scenario 4: Binge Watching Session

**Description**: User watches multiple episodes back-to-back on a tablet.

### Episode 1 Complete
```json
{
  "event_id": "EVENT_bing1234",
  "customer_id": "CUST_weekend1",
  "title_id": "TITLE_series_s02e01",
  "session_id": "SESSION_tab11111",
  "event_type": "complete",
  "event_timestamp": "2025-08-11T14:45:00.000Z",
  "watch_duration_seconds": 2700,
  "position_seconds": 2700,
  "completion_percentage": 100.0,
  "device_type": "tablet",
  "device_id": "DEVICE_ipad9876",
  "device_os": "iOS",
  "app_version": "5.2.1",
  "quality": "HD",
  "bandwidth_mbps": 25.5,
  "buffering_events": 0,
  "buffering_duration_seconds": 0,
  "error_count": 0,
  "ip_address": "192.168.1.45",
  "country": "Canada",
  "state": "Ontario",
  "city": "Toronto",
  "isp": "Rogers",
  "connection_type": "wifi"
}
```

### Episode 2 Start (Auto-play)
```json
{
  "event_id": "EVENT_bing2345",
  "customer_id": "CUST_weekend1",
  "title_id": "TITLE_series_s02e02",
  "session_id": "SESSION_tab22222",
  "event_type": "start",
  "event_timestamp": "2025-08-11T14:45:10.000Z",
  "watch_duration_seconds": 0,
  "position_seconds": 0,
  "completion_percentage": 0.0,
  "device_type": "tablet",
  "device_id": "DEVICE_ipad9876",
  "device_os": "iOS",
  "app_version": "5.2.1",
  "quality": "HD",
  "bandwidth_mbps": 24.8,
  "buffering_events": 0,
  "buffering_duration_seconds": 0,
  "error_count": 0,
  "ip_address": "192.168.1.45",
  "country": "Canada",
  "state": "Ontario",
  "city": "Toronto",
  "isp": "Rogers",
  "connection_type": "wifi"
}
```

---

## Scenario 5: Resume Watching Across Devices

**Description**: User starts watching on phone, continues on TV.

### Mobile Session End
```json
{
  "event_id": "EVENT_cross123",
  "customer_id": "CUST_multi456",
  "title_id": "TITLE_movie_789",
  "session_id": "SESSION_mob33333",
  "event_type": "stop",
  "event_timestamp": "2025-08-11T18:30:00.000Z",
  "watch_duration_seconds": 1800,
  "position_seconds": 1800,
  "completion_percentage": 30.0,
  "device_type": "mobile",
  "device_id": "DEVICE_and45678",
  "device_os": "Android",
  "app_version": "5.1.8",
  "quality": "SD",
  "bandwidth_mbps": 8.5,
  "buffering_events": 1,
  "buffering_duration_seconds": 2,
  "error_count": 0,
  "ip_address": "70.123.45.67",
  "country": "United States",
  "state": "Texas",
  "city": "Austin",
  "isp": "AT&T",
  "connection_type": "mobile"
}
```

### TV Session Start (Resume Position)
```json
{
  "event_id": "EVENT_cross456",
  "customer_id": "CUST_multi456",
  "title_id": "TITLE_movie_789",
  "session_id": "SESSION_tv444444",
  "event_type": "start",
  "event_timestamp": "2025-08-11T19:15:00.000Z",
  "watch_duration_seconds": 0,
  "position_seconds": 1800,
  "completion_percentage": 30.0,
  "device_type": "tv",
  "device_id": "DEVICE_fire7890",
  "device_os": "Fire TV",
  "app_version": "5.2.0",
  "quality": "4K",
  "bandwidth_mbps": 85.0,
  "buffering_events": 0,
  "buffering_duration_seconds": 0,
  "error_count": 0,
  "ip_address": "70.123.45.67",
  "country": "United States",
  "state": "Texas",
  "city": "Austin",
  "isp": "AT&T",
  "connection_type": "fiber"
}
```

---

## Scenario 6: Error and Recovery

**Description**: User experiences errors but continues watching.

```json
{
  "event_id": "EVENT_err78901",
  "customer_id": "CUST_persist1",
  "title_id": "TITLE_live_sport",
  "session_id": "SESSION_err55555",
  "event_type": "stop",
  "event_timestamp": "2025-08-11T21:00:00.000Z",
  "watch_duration_seconds": 5400,
  "position_seconds": 5400,
  "completion_percentage": 60.0,
  "device_type": "web",
  "device_id": "DEVICE_mac12345",
  "device_os": "macOS",
  "app_version": "5.0.0",
  "quality": "HD",
  "bandwidth_mbps": 15.5,
  "buffering_events": 8,
  "buffering_duration_seconds": 45,
  "error_count": 5,
  "ip_address": "24.56.78.90",
  "country": "United Kingdom",
  "state": "",
  "city": "London",
  "isp": "Virgin Media",
  "connection_type": "cable"
}
```

---

## Batch Data Example

**Description**: Multiple events in a single Kafka batch (JSON Lines format).

```json
{"event_id":"EVENT_batch001","customer_id":"CUST_user001","title_id":"TITLE_cont001","session_id":"SESSION_a1b2c3d4","event_type":"start","event_timestamp":"2025-08-11T10:00:00.000Z","watch_duration_seconds":0,"position_seconds":0,"completion_percentage":0.0,"device_type":"mobile","device_id":"DEVICE_mob11111","device_os":"iOS","app_version":"5.2.1","quality":"HD","bandwidth_mbps":20.5,"buffering_events":0,"buffering_duration_seconds":0,"error_count":0,"ip_address":"192.168.1.100","country":"United States","state":"California","city":"Los Angeles","isp":"Spectrum","connection_type":"wifi"}
{"event_id":"EVENT_batch002","customer_id":"CUST_user002","title_id":"TITLE_cont002","session_id":"SESSION_e5f6g7h8","event_type":"pause","event_timestamp":"2025-08-11T10:00:01.000Z","watch_duration_seconds":600,"position_seconds":600,"completion_percentage":20.0,"device_type":"tv","device_id":"DEVICE_tv222222","device_os":"Roku OS","app_version":"5.2.0","quality":"4K","bandwidth_mbps":50.0,"buffering_events":0,"buffering_duration_seconds":0,"error_count":0,"ip_address":"10.0.0.50","country":"Canada","state":"Quebec","city":"Montreal","isp":"Bell","connection_type":"fiber"}
{"event_id":"EVENT_batch003","customer_id":"CUST_user003","title_id":"TITLE_cont003","session_id":"SESSION_i9j0k1l2","event_type":"complete","event_timestamp":"2025-08-11T10:00:02.000Z","watch_duration_seconds":3600,"position_seconds":3600,"completion_percentage":100.0,"device_type":"web","device_id":"DEVICE_web33333","device_os":"Windows","app_version":"5.1.9","quality":"HD","bandwidth_mbps":15.0,"buffering_events":2,"buffering_duration_seconds":5,"error_count":0,"ip_address":"172.16.0.1","country":"United States","state":"New York","city":"Buffalo","isp":"Frontier","connection_type":"cable"}
```

---

## Data Patterns and Statistics

### Event Type Distribution (Daily)
- `start`: 25%
- `stop`: 35%
- `pause`: 15%
- `resume`: 15%
- `complete`: 10%

### Device Type Distribution
- `mobile`: 35%
- `tv`: 30%
- `web`: 25%
- `tablet`: 10%

### Quality Distribution
- `SD`: 25%
- `HD`: 60%
- `4K`: 15%

### Average Metrics
- **Watch Duration**: 1800 seconds (30 minutes)
- **Completion Rate**: 65%
- **Buffering Events**: 1.5 per session
- **Error Rate**: 0.2 per session

### Peak Times (UTC)
- **Morning Peak**: 11:00 - 14:00 (5,000-10,000 viewers)
- **Evening Peak**: 18:00 - 22:00 (15,000-25,000 viewers)
- **Late Night**: 02:00 - 06:00 (2,000-5,000 viewers)

---

## Validation Test Cases

### Test Case 1: Valid Start Event
- `event_type` = "start"
- `watch_duration_seconds` = 0
- `position_seconds` >= 0
- All required fields present

### Test Case 2: Invalid Duration
- `watch_duration_seconds` > 86400 (Should fail validation)

### Test Case 3: Bandwidth-Quality Mismatch
- `quality` = "4K"
- `bandwidth_mbps` < 15.0 (Should trigger warning)

### Test Case 4: Buffering Logic
- If `buffering_events` = 0, then `buffering_duration_seconds` must = 0

### Test Case 5: Completion Logic
- If `event_type` = "complete", then `completion_percentage` should be > 90.0

---

## Notes

1. **Session Continuity**: All events within a session should have the same `session_id`, `customer_id`, and `device_id`
2. **Timestamp Ordering**: Events should arrive in chronological order within a session
3. **Network Changes**: IP address and bandwidth may change during mobile sessions
4. **Auto-play**: Back-to-back episodes may have very short gaps (< 15 seconds)
5. **Cross-device Resume**: Position may be preserved when switching devices

---

## Contact

For questions about sample data:
- **Team**: Data Engineering
- **Documentation**: See STREAMING_DATA_SCHEMA.md and DATA_DICTIONARY.md