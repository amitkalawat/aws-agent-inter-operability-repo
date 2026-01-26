# Architecture Documentation

## System Architecture

### Overview

This solution implements a real-time data streaming infrastructure using Amazon MSK (Managed Streaming for Apache Kafka) for data ingestion with S3 storage for logs and data.

```
┌─────────────────────────────────────────────────────────────┐
│                    Producer Applications                      │
│  (Python/Java/Node.js clients with IAM authentication)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Amazon MSK Cluster                          │
│  • 3 brokers (kafka.m5.large)                               │
│  • SASL/IAM authentication                                   │
│  • TLS encryption in-transit                                │
│  • Private subnets                                          │
│  • Multi-VPC connectivity enabled                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS PrivateLink / Multi-VPC                     │
│  (Enables private connectivity for services)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Amazon S3 Storage                        │
│  • Log storage and data archival                            │
│  • Lifecycle policies for cost optimization                  │
│  • Server-side encryption                                   │
│  • Versioning enabled                                       │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Amazon MSK Cluster

**Purpose**: Central message broker for real-time data streaming

**Configuration**:
- **Instance Type**: kafka.m5.large (3 brokers)
- **Storage**: 100GB EBS per broker
- **Kafka Version**: 3.5.1
- **Availability**: Deployed across 3 AZs
- **Networking**: Private subnets only

**Security**:
- SASL/IAM authentication (no passwords)
- TLS 1.2 encryption for all connections
- Security groups restrict access
- CloudTrail logging for audit


### 2. Multi-VPC Connectivity

**Purpose**: Enable secure private connectivity between MSK and AWS services

**Why Required**:
- MSK in private subnets cannot use PUBLIC connectivity
- Avoids exposing MSK to internet
- Enables cross-VPC access

**Benefits**:
- No data transfer costs within region
- Lower latency
- Enhanced security
- Support for cross-VPC access

### 3. Amazon S3 Storage

**Purpose**: Log storage and data archival

**Structure**:
```
s3://msk-data-{account}-{region}/
└── msk-logs/
    └── broker-logs/
```

**Features**:
- Lifecycle policies for cost management
- Compatible with analytics services
- Versioning for data protection

## Data Flow

### 1. Data Ingestion

```python
Producer App → MSK Broker → Kafka Topic
```

- Producers authenticate using IAM
- Data distributed across partitions
- Replicated across 3 brokers

### 2. Direct Consumer Access

```python
MSK Topic → Consumer Application
```

- Consumers can read directly from MSK
- Real-time processing capability
- Multiple consumer groups supported

## Network Architecture

### VPC Configuration

```
VPC (10.0.0.0/16)
├── Private Subnet 1 (10.0.1.0/24) - AZ 1
│   └── MSK Broker 1
├── Private Subnet 2 (10.0.2.0/24) - AZ 2
│   └── MSK Broker 2
└── Private Subnet 3 (10.0.3.0/24) - AZ 3
    └── MSK Broker 3
```

### Security Groups

**MSK Security Group**:
- Inbound: Port 9098 from VPC CIDR
- Outbound: All traffic allowed

**Application Security Group**:
- Outbound: Port 9098 to MSK

## Authentication & Authorization

### IAM Authentication Flow

```
1. Client requests auth token from STS
2. STS validates IAM credentials
3. Client presents token to MSK
4. MSK validates token with IAM
5. Connection established
```

### Required IAM Permissions

**Producer/Consumer**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kafka-cluster:Connect",
        "kafka-cluster:AlterCluster",
        "kafka-cluster:DescribeCluster"
      ],
      "Resource": "arn:aws:kafka:*:*:cluster/simple-msk-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kafka-cluster:ReadData",
        "kafka-cluster:WriteData",
        "kafka-cluster:DescribeTopic"
      ],
      "Resource": "arn:aws:kafka:*:*:topic/simple-msk-*/*/*"
    }
  ]
}
```

## Scalability Considerations

### Horizontal Scaling

**MSK**:
- Add more brokers (up to 15 per cluster)
- Increase partitions per topic
- Add read replicas for consumers

### Vertical Scaling

**MSK**:
- Change instance types (requires downtime)
- Current: m5.large → Possible: m5.xlarge, m5.2xlarge

### Storage Scaling

**MSK**:
- Can increase storage without downtime
- Current: 100GB → Max: 16TB per broker

**S3**:
- Unlimited storage capacity
- Lifecycle policies manage costs

## Monitoring & Observability

### CloudWatch Metrics

**MSK Metrics**:
- CPU utilization
- Network throughput
- Disk usage
- Consumer lag

### CloudWatch Logs

**Log Groups**:
- `/aws/msk/simple-msk-us-west-2` - MSK broker logs

### Alarms

Recommended alarms:
1. MSK CPU > 80%
2. Disk usage > 80%
3. Consumer lag > 10000 messages

## Disaster Recovery

### Backup Strategy

**MSK**:
- Topic configuration backed up in CDK
- Data replicated across 3 AZs
- Point-in-time recovery via S3

**S3**:
- Versioning enabled
- Cross-region replication available
- 99.999999999% durability

### Recovery Procedures

**Broker Failure**:
- Automatic failover to replica
- No data loss with RF=3
- ~30 second recovery time

**AZ Failure**:
- Cluster continues with 2 brokers
- Automatic rebalancing
- No data loss

**Region Failure**:
- Deploy stack in new region
- Restore from S3 backups
- Update DNS/endpoints

## Cost Optimization

### Current Costs (Estimated)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| MSK | 3 × m5.large | ~$450 |
| MSK Storage | 300GB | ~$30 |
| S3 Storage | 1TB | ~$23 |
| Data Transfer | In-region | $0 |
| **Total** | | **~$503** |

### Optimization Strategies

1. **Right-sizing**:
   - Monitor actual usage
   - Downsize if overprovisioned
   - Use Reserved Instances

2. **Storage Optimization**:
   - S3 lifecycle policies
   - Intelligent Tiering
   - Delete old data

3. **Data Compression**:
   - GZIP reduces storage 60-70%
   - Lower transfer costs

## Security Best Practices

### Network Security

✅ Private subnets only
✅ No internet gateway attached
✅ VPC endpoints for AWS services
✅ Security groups with least privilege

### Data Security

✅ Encryption in transit (TLS)
✅ Encryption at rest (S3 SSE)
✅ No hardcoded credentials
✅ IAM authentication only

### Access Control

✅ Principle of least privilege
✅ Separate roles for producers/consumers
✅ CloudTrail audit logging
✅ No public access

## Future Enhancements

### Short Term (1-3 months)

1. **Schema Registry**:
   - Add Confluent Schema Registry
   - Enforce data contracts
   - Version management

2. **Monitoring Dashboard**:
   - Custom CloudWatch dashboard
   - Grafana integration
   - Alert automation

### Medium Term (3-6 months)

1. **Stream Processing**:
   - Add Kinesis Analytics
   - Real-time aggregations
   - Anomaly detection

2. **Data Catalog**:
   - AWS Glue catalog
   - Automated crawlers
   - Athena queries

### Long Term (6-12 months)

1. **Multi-Region**:
   - Active-active setup
   - Global data replication
   - Disaster recovery automation

2. **ML Integration**:
   - SageMaker pipelines
   - Real-time predictions
   - Feature store

## Compliance Considerations

### Data Governance

- **Data Retention**: Configurable per topic
- **Data Deletion**: Automated via lifecycle
- **Data Lineage**: CloudTrail + S3 access logs

### Regulatory Compliance

- **GDPR**: Data deletion capabilities
- **HIPAA**: Encryption at rest/transit
- **SOC2**: Audit logging enabled

## Appendix

### Useful Commands

```bash
# Check cluster status
aws kafka describe-cluster --cluster-arn <ARN>

# List topics (from EC2 in VPC)
kafka-topics.sh --list --bootstrap-server <BROKERS>

# Check S3 data
aws s3 ls s3://msk-data-<ACCOUNT>-<REGION>/ --recursive
```

### References

- [MSK Best Practices](https://docs.aws.amazon.com/msk/latest/developerguide/best-practices.html)
- [S3 Performance](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html)