# MSK Cluster with CDK

This repository contains AWS CDK infrastructure code for setting up an Amazon MSK (Managed Streaming for Apache Kafka) cluster with S3 storage for logs and data.

## Architecture Overview

```
Producer Applications
        ↓
Amazon MSK Cluster (Private Subnets)
        ↓
[Multi-VPC Connectivity / PrivateLink]
        ↓
Amazon S3 Data Storage
```

## Project Structure

```
.
├── bin/
│   ├── simple-msk.ts              # Main CDK app entry point (current)
│   └── msk-s3-pipeline.ts         # MSK pipeline app
├── lib/
│   ├── simple-msk-stack.ts        # Simplified MSK stack (DEPLOYED)
│   ├── msk-to-s3-stack.ts        # MSK to S3 stack
│   └── constructs/
│       └── msk-cluster.ts         # MSK cluster construct
├── scripts/
│   └── enable-multi-vpc.sh        # Script to enable Multi-VPC connectivity
├── test/
│   └── msk-to-s3-stack.test.ts   # Unit tests
└── docs/
    └── DEPLOYMENT.md              # Detailed deployment guide
```

## Current Deployment Status (us-west-2)

✅ **DEPLOYED**: SimpleMskStack
- **MSK Cluster ARN**: `arn:aws:kafka:us-west-2:878687028155:cluster/simple-msk-us-west-2/05a8cbf7-ea44-42d5-a3ca-2d78cc557cc5-6`
- **S3 Bucket**: `msk-data-878687028155-us-west-2`
- **VPC**: `vpc-0532139c684f64fda` (llamaindex-vpc)
- **Region**: us-west-2
- **Authentication**: SASL/IAM
- **Multi-VPC Connectivity**: ENABLED ✅

## Prerequisites

- Node.js 18.x or later
- AWS CDK CLI 2.x (`npm install -g aws-cdk`)
- AWS CLI configured with appropriate credentials
- An existing VPC in your target region

## Installation

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build
```

## Deployment

### Deploy MSK Cluster

```bash
# Deploy to us-west-2 (or any region)
npx cdk deploy -c vpcId=vpc-xxxxxxxxx -c region=us-west-2 --require-approval never
```

### Enable Multi-VPC Connectivity

```bash
# Run after MSK cluster is ACTIVE
./scripts/enable-multi-vpc.sh
```

## Key Learnings & Constraints

### MSK Public Access Limitations
- ❌ Public access CANNOT be enabled during cluster creation
- ❌ Public access requires cluster to be in PUBLIC subnets
- ✅ Use Multi-VPC connectivity for private subnet clusters

### Solution Approach
1. Create MSK cluster in private subnets (secure)
2. Enable Multi-VPC connectivity after cluster creation
3. All traffic stays within AWS network

## Configuration

### MSK Cluster Settings
- **Instance Type**: kafka.m5.large (3 brokers)
- **Storage**: 100GB EBS per broker
- **Monitoring**: CloudWatch & S3 logs
- **Encryption**: TLS in-transit
- **Kafka Version**: 3.5.1

### S3 Data Storage
- **Versioning**: Enabled
- **Lifecycle**: 
  - 30 days → Infrequent Access
  - 90 days → Glacier
- **Partitioning**: By year/month/day/hour
- **Compression**: GZIP

## Connecting to MSK

### Bootstrap Servers
```
b-2.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098,
b-1.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098,
b-3.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098
```

### Producer Configuration (Java/Python)
```properties
bootstrap.servers=<see above>
security.protocol=SASL_SSL
sasl.mechanism=AWS_MSK_IAM
sasl.jaas.config=software.amazon.msk.auth.iam.IAMLoginModule required;
```


## Monitoring

### CloudWatch Dashboard
Access via AWS Console → CloudWatch → Dashboards → MSK-S3-Pipeline-us-west-2

### Key Metrics
- MSK CPU Utilization
- Bytes In/Out per second
- S3 PUT request metrics

## Troubleshooting

### Common Issues

1. **Cannot enable public access**
   - Cause: Cluster is in private subnets
   - Solution: Use Multi-VPC connectivity

2. **IAM authentication fails**
   - Check IAM role has `kafka-cluster:*` permissions
   - Ensure using port 9098 for IAM

## Clean Up

```bash
# Delete all resources
npx cdk destroy --force
```

## Cost Optimization

- MSK: ~$0.21/hour for m5.large (x3 brokers)
- S3: Pay per GB stored + lifecycle transitions
- Data transfer: Free within same region

## Security Best Practices

- ✅ MSK in private subnets
- ✅ IAM authentication (no passwords)
- ✅ TLS encryption in transit
- ✅ S3 server-side encryption
- ✅ VPC endpoints for private connectivity
- ✅ CloudTrail logging enabled

## Next Steps

1. Create producer applications
2. Set up consumer applications
3. Configure data retention policies
4. Set up alerting for failures
5. Implement data validation/transformation

## License

MIT

## Support

For issues or questions, please create an issue in this repository.