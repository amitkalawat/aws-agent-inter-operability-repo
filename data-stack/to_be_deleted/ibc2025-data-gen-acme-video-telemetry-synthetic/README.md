# ACME Telemetry Pipeline

Real-time telemetry generation and processing system for ACME streaming platform using AWS services.

## 🏗️ Architecture

```
EventBridge (5 min) → Lambda Generator → Lambda Producer → MSK → Firehose → S3
```

- **EventBridge**: Triggers telemetry generation every 5 minutes
- **Lambda Generator**: Creates 2,000-25,000 realistic viewer telemetry events
- **Lambda Producer**: Publishes events to Amazon MSK with IAM authentication
- **Amazon MSK**: Kafka cluster for real-time event streaming
- **Kinesis Firehose**: Consumes from MSK and delivers to S3
- **S3 Data Lake**: Stores compressed telemetry data with partitioning

## 📁 Repository Structure

```
.
├── README.md                           # This file
├── lambda/
│   ├── telemetry_generator/
│   │   └── handler.py                  # Generates telemetry events
│   └── msk_producer/
│       ├── handler.py                  # Sends events to MSK
│       └── requirements.txt            # Python dependencies
├── scripts/
│   └── create_msk_topic.py            # Creates Kafka topic in MSK
├── config/
│   ├── msk-cluster-policy.json        # MSK cluster policy for Firehose
│   └── firehose-config.json           # Firehose delivery stream config
└── docs/
    ├── DEPLOYMENT_GUIDE.md             # Complete deployment instructions
    └── TELEMETRY_SCHEMA.md             # Telemetry data schema documentation
```

## 🚀 Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- MSK Cluster with IAM authentication enabled
- VPC with private subnets and NAT Gateway
- S3 bucket for data storage

### Deployment Steps

1. **Create MSK Topic**
```bash
python scripts/create_msk_topic.py
```

2. **Deploy Lambda Functions**
```bash
# Package and deploy Generator
cd lambda/telemetry_generator
zip -r ../../generator.zip .
aws lambda create-function --function-name AcmeTelemetry-Generator \
  --runtime python3.9 --handler handler.lambda_handler \
  --zip-file fileb://../../generator.zip

# Package and deploy Producer
cd ../msk_producer
pip install -r requirements.txt -t .
zip -r ../../producer.zip .
aws lambda create-function --function-name AcmeTelemetry-Producer \
  --runtime python3.9 --handler handler.lambda_handler \
  --zip-file fileb://../../producer.zip
```

3. **Configure MSK Cluster Policy**
```bash
aws kafka put-cluster-policy --cluster-arn <MSK_CLUSTER_ARN> \
  --policy file://config/msk-cluster-policy.json
```

4. **Create Firehose Delivery Stream**
```bash
aws firehose create-delivery-stream \
  --cli-input-json file://config/firehose-config.json
```

5. **Set up EventBridge Schedule**
```bash
aws events put-rule --name AcmeTelemetry-GeneratorSchedule \
  --schedule-expression "rate(5 minutes)" --state ENABLED
```

For detailed deployment instructions, see [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md).

## 📊 Telemetry Schema

The system generates telemetry events with 24 fields capturing:
- User and session information
- Viewing behavior and progress
- Device and application details
- Network and quality metrics
- Geographic information

See [docs/TELEMETRY_SCHEMA.md](docs/TELEMETRY_SCHEMA.md) for complete schema documentation.

## 🔧 Configuration

### Environment Variables

**Generator Lambda:**
- `MSK_PRODUCER_FUNCTION_NAME`: Name of the Producer Lambda function

**Producer Lambda:**
- `MSK_CLUSTER_ARN`: ARN of the MSK cluster
- `TOPIC_NAME`: Kafka topic name (default: `acme-telemetry`)
- `AWS_DEFAULT_REGION`: AWS region (default: `us-west-2`)

### Firehose Configuration
- Buffer Time: 5 minutes
- Buffer Size: 128 MB
- Compression: GZIP
- Partitioning: `year/month/day/hour`

## 📈 Monitoring

### CloudWatch Metrics
- Lambda invocations and errors
- Firehose IncomingRecords
- MSK cluster metrics

### CloudWatch Logs
- `/aws/lambda/AcmeTelemetry-Generator`
- `/aws/lambda/AcmeTelemetry-Producer`
- `/aws/kinesisfirehose/AcmeTelemetry-MSK-to-S3`

## 🧪 Testing

### Manual Testing
```bash
# Test telemetry generation
aws lambda invoke --function-name AcmeTelemetry-Generator \
  --payload '{"test": true, "batch_size": 100}' \
  --cli-binary-format raw-in-base64-out output.json

# Check S3 for data (after 5 min buffer)
aws s3 ls s3://your-bucket/telemetry/ --recursive
```

## 📝 Data Output

Data is stored in S3 with:
- **Format**: GZIP compressed JSON
- **Partitioning**: `telemetry/year=YYYY/month=MM/day=DD/hour=HH/`
- **File naming**: `AcmeTelemetry-MSK-to-S3-{partition}-{timestamp}-{uuid}.gz`

### Sample Data
```json
{
  "event_id": "EVENT_a1b2c3d4",
  "customer_id": "CUST_5e6f7g8h",
  "title_id": "TITLE_9i0j1k2l",
  "session_id": "SESSION_3m4n5o6p",
  "event_type": "start",
  "event_timestamp": "2025-08-11T14:30:45.123Z",
  "watch_duration_seconds": 1800,
  "position_seconds": 900,
  "completion_percentage": 45.5,
  "device_type": "mobile",
  "device_os": "iOS",
  "quality": "HD",
  "bandwidth_mbps": 8.5,
  ...
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Lambda timeout connecting to MSK**
   - Ensure Lambda is in the same VPC as MSK
   - Check security group allows port 9098

2. **No data in S3**
   - Wait for Firehose buffer time (5 minutes)
   - Check MSK topic exists
   - Verify Firehose IAM role permissions

3. **Firehose not consuming from MSK**
   - Ensure topic exists before creating Firehose
   - Check MSK cluster policy

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md#troubleshooting) for more details.

## 📄 License

Copyright 2025 ACME Corporation. All rights reserved.

## 🤝 Contributing

For questions or issues, please contact the Data Engineering team.

## 📚 Additional Resources

- [AWS MSK Documentation](https://docs.aws.amazon.com/msk/)
- [Kinesis Data Firehose Documentation](https://docs.aws.amazon.com/firehose/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)