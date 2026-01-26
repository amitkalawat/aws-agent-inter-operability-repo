# ACME Telemetry Pipeline - Quick Reference

## Common Commands

### Generate Test Data
```bash
# Small batch (100 events)
aws lambda invoke \
  --function-name AcmeTelemetry-Generator \
  --payload '{"test": true, "batch_size": 100}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/output.json \
  --region eu-central-1

# Large batch (1000 events)
aws lambda invoke \
  --function-name AcmeTelemetry-Generator \
  --payload '{"test": true, "batch_size": 1000}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/output.json \
  --region eu-central-1
```

### Check Pipeline Status
```bash
# View Lambda logs
aws logs tail /aws/lambda/AcmeTelemetry-Generator --follow --region eu-central-1
aws logs tail /aws/lambda/AcmeTelemetry-Producer --follow --region eu-central-1
aws logs tail /aws/lambda/AcmeTelemetry-DataLoader --follow --region eu-central-1

# Check S3 data
aws s3 ls s3://acme-telemetry-241533163649-eu-central-1/telemetry/ \
  --recursive --region eu-central-1 | tail -10

# Monitor Firehose
aws firehose describe-delivery-stream \
  --delivery-stream-name AcmeTelemetry-MSK-to-S3 \
  --region eu-central-1 \
  --query 'DeliveryStreamDescription.DeliveryStreamStatus'
```

### Athena Quick Queries

#### Today's Event Count
```sql
SELECT COUNT(*) as total_events
FROM acme_telemetry.video_telemetry_json
WHERE year = YEAR(CURRENT_DATE) 
  AND month = MONTH(CURRENT_DATE) 
  AND day = DAY(CURRENT_DATE);
```

#### Top 5 Titles Today
```sql
SELECT 
    t.title_name,
    COUNT(*) as views
FROM acme_telemetry.video_telemetry_json vt
JOIN acme_streaming_data.titles t ON vt.title_id = t.title_id
WHERE vt.year = YEAR(CURRENT_DATE) 
  AND vt.month = MONTH(CURRENT_DATE) 
  AND vt.day = DAY(CURRENT_DATE)
GROUP BY t.title_name
ORDER BY views DESC
LIMIT 5;
```

#### Current Hour Activity
```sql
SELECT 
    COUNT(*) as events,
    COUNT(DISTINCT customer_id) as active_users
FROM acme_telemetry.video_telemetry_json
WHERE year = YEAR(CURRENT_DATE) 
  AND month = MONTH(CURRENT_DATE) 
  AND day = DAY(CURRENT_DATE)
  AND hour = HOUR(CURRENT_TIMESTAMP);
```

### Troubleshooting

#### Repair Partitions
```bash
aws athena start-query-execution \
  --query-string "MSCK REPAIR TABLE acme_telemetry.video_telemetry_json" \
  --query-execution-context "Database=acme_telemetry" \
  --result-configuration "OutputLocation=s3://acme-telemetry-241533163649-eu-central-1/athena-results/" \
  --region eu-central-1
```

#### Force Refresh Reference Data
```bash
aws lambda invoke \
  --function-name AcmeTelemetry-DataLoader \
  --payload '{"force_refresh": true}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/refresh.json \
  --region eu-central-1
```

#### Run Glue Crawler Manually
```bash
aws glue start-crawler \
  --name AcmeTelemetry-S3-Crawler \
  --region eu-central-1
```

#### Check MSK Topic
```bash
# Get bootstrap servers
aws kafka get-bootstrap-brokers \
  --cluster-arn arn:aws:kafka:eu-central-1:241533163649:cluster/simple-msk-eu-central-1/26147c0d-2edc-4f80-9428-346a44b1659e-2 \
  --region eu-central-1
```

### Update Lambda Functions
```bash
# Update all functions
cd /path/to/repo
./scripts/deploy_lambdas.sh

# Update individual function
cd lambda/telemetry_generator
zip -r ../../generator.zip . -q
aws lambda update-function-code \
  --function-name AcmeTelemetry-Generator \
  --zip-file fileb://../../generator.zip \
  --region eu-central-1
```

### Monitor Costs
```bash
# Check S3 storage
aws s3api list-buckets --query 'Buckets[?contains(Name, `acme-telemetry`)]'
aws s3 ls s3://acme-telemetry-241533163649-eu-central-1/ --recursive --summarize --human-readable

# Check Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=AcmeTelemetry-Generator \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --region eu-central-1
```

## Environment Variables

### Generator Lambda
- `MSK_PRODUCER_FUNCTION_NAME`: AcmeTelemetry-Producer
- `DATA_LOADER_FUNCTION_NAME`: AcmeTelemetry-DataLoader

### Producer Lambda
- `MSK_CLUSTER_ARN`: arn:aws:kafka:eu-central-1:241533163649:cluster/simple-msk-eu-central-1/...
- `TOPIC_NAME`: acme-telemetry

## Key Resources

### S3 Buckets
- **Telemetry Data**: `s3://acme-telemetry-241533163649-eu-central-1/telemetry/`
- **Athena Results**: `s3://acme-telemetry-241533163649-eu-central-1/athena-results/`
- **Reference Cache**: `s3://acme-telemetry-241533163649-eu-central-1/cache/`

### Databases
- **Telemetry**: `acme_telemetry.video_telemetry_json`
- **Reference**: `acme_streaming_data.titles`, `acme_streaming_data.customers`

### Lambda Functions
- `AcmeTelemetry-Generator`
- `AcmeTelemetry-Producer`
- `AcmeTelemetry-DataLoader`

### IAM Roles
- `AcmeTelemetry-Generator-Role`
- `AcmeTelemetry-Producer-Role`
- `AcmeTelemetry-DataLoader-Role`
- `AcmeTelemetry-Firehose-Role`
- `AcmeTelemetry-GlueCrawler-Role`

## Data Schema

### Telemetry Event
```json
{
  "event_id": "EVENT_abc12345",
  "customer_id": "CUST_17125cf4_099233",
  "title_id": "TITLE_0afcc18c_004133",
  "session_id": "SESSION_xyz98765",
  "event_type": "start|stop|pause|resume|complete",
  "event_timestamp": "2025-08-11T18:30:00Z",
  "watch_duration_seconds": 1800,
  "position_seconds": 900,
  "completion_percentage": 50.0,
  "device_type": "mobile|web|tv|tablet",
  "device_id": "DEVICE_def45678",
  "device_os": "iOS|Android|Windows|macOS|Roku OS",
  "app_version": "2.1.45",
  "quality": "SD|HD|4K",
  "bandwidth_mbps": 15.5,
  "buffering_events": 2,
  "buffering_duration_seconds": 10,
  "error_count": 0,
  "ip_address": "192.168.1.1",
  "country": "United States",
  "state": "California",
  "city": "Los Angeles",
  "isp": "Comcast",
  "connection_type": "wifi|mobile|fiber|cable"
}
```

## Support Scripts

- `scripts/deploy_lambdas.sh` - Deploy all Lambda functions
- `scripts/create_iam_roles.sh` - Create IAM roles
- `scripts/setup_eventbridge.sh` - Configure EventBridge schedule
- `scripts/test_queries.sh` - Run sample Athena queries
- `scripts/create_firehose.sh` - Create Kinesis Firehose