# Deployment Guide

## Complete Deployment Walkthrough

### Step 1: Prerequisites

Ensure you have:
- AWS CLI configured with appropriate credentials
- Node.js 18+ and npm installed
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- A VPC in your target region

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd ibc2025-data-gen-realtime-repo-v2

# Install dependencies
npm install

# Build the TypeScript code
npm run build
```

### Step 3: Deploy MSK Cluster

```bash
# Set your VPC ID and region
export VPC_ID="vpc-0532139c684f64fda"  # Replace with your VPC ID
export AWS_REGION="us-west-2"           # Replace with your region

# Deploy the stack
npx cdk deploy -c vpcId=$VPC_ID -c region=$AWS_REGION --require-approval never
```

This will create:
- MSK cluster with 3 brokers
- S3 bucket for data storage
- CloudWatch log groups
- Security groups and IAM roles

**Expected time**: ~25-30 minutes

### Step 4: Enable Multi-VPC Connectivity

After the MSK cluster is ACTIVE:

```bash
# Make the script executable
chmod +x scripts/enable-multi-vpc.sh

# Run the script
./scripts/enable-multi-vpc.sh
```

**Expected time**: ~5-10 minutes

### Step 5: Verify Deployment


```bash
# Check MSK cluster status
aws kafka describe-cluster \
  --cluster-arn arn:aws:kafka:us-west-2:878687028155:cluster/simple-msk-us-west-2/05a8cbf7-ea44-42d5-a3ca-2d78cc557cc5-6 \
  --region us-west-2 \
  --query 'ClusterInfo.State'

# Check S3 bucket
aws s3 ls s3://msk-data-878687028155-us-west-2/
```

## Architecture Decisions

### Why Private Subnets?

- **Security**: MSK cluster is not exposed to the internet
- **Compliance**: Many organizations require data infrastructure in private subnets
- **Cost**: No NAT gateway charges for public IPs

### Why Multi-VPC Connectivity?

- **Future Flexibility**: Allows cross-VPC access if needed
- **Security**: No public exposure required
- **Service Integration**: Enables private connectivity with AWS services

### Why IAM Authentication?

- **No Password Management**: Uses AWS IAM for authentication
- **Fine-grained Access Control**: IAM policies for topic-level permissions
- **Audit Trail**: CloudTrail logs all access

## Troubleshooting Guide

### Issue: Cannot Connect to MSK

**Symptoms**:
- Connection timeout when connecting to cluster

**Solution**:
1. Ensure you're running commands from within the VPC
2. Check security group allows port 9098
3. Verify IAM permissions include `kafka-cluster:*`

## Production Considerations

### High Availability

- Deploy across 3 availability zones
- Use 3 brokers minimum (current configuration)
- Set replication factor to 3 for topics

### Monitoring

Set up CloudWatch alarms for:
- MSK CPU utilization > 80%
- S3 PUT errors
- Disk usage > 80%
- Consumer lag > threshold

### Scaling

- **Vertical**: Change instance type (requires cluster recreation)
- **Horizontal**: Add more brokers (supported via console/CLI)
- **Storage**: Can be increased without downtime

### Backup and Recovery

- Enable S3 versioning (already configured)
- Set up S3 cross-region replication for DR
- Regular snapshots of MSK configuration

### Cost Optimization

1. **Right-size instances**: Start with m5.large, monitor usage
2. **Lifecycle policies**: Move old data to cheaper storage (configured)
3. **Reserved Instances**: For predictable workloads
4. **Data compression**: GZIP compression enabled

## Security Hardening

### Network Security

```bash
# Restrict security group to specific CIDR blocks
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxx \
  --protocol tcp \
  --port 9098 \
  --source-group sg-yyyyyy  # Application security group
```

### IAM Least Privilege

Create topic-specific policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "kafka-cluster:Connect",
      "kafka-cluster:DescribeTopic"
    ],
    "Resource": [
      "arn:aws:kafka:*:*:cluster/*/topic/events"
    ]
  }]
}
```

### Encryption

- **In-transit**: TLS enabled (configured)
- **At-rest**: EBS encryption (can be enabled)
- **S3**: Server-side encryption (configured)

## Maintenance

### Regular Tasks

- **Weekly**: Review CloudWatch metrics
- **Monthly**: Check S3 lifecycle transitions
- **Quarterly**: Review and optimize costs

### Upgrade Path

1. Test upgrades in development environment
2. Schedule maintenance window
3. Update one broker at a time
4. Verify client compatibility

## Support Matrix

| Component | Version | Support Until |
|-----------|---------|---------------|
| Kafka | 3.5.1 | Active |
| CDK | 2.150.0 | Active |
| Node.js | 18.x | April 2025 |
| AWS MSK | Latest | N/A |

## References

- [AWS MSK Documentation](https://docs.aws.amazon.com/msk/)
- [MSK IAM Authentication](https://docs.aws.amazon.com/msk/latest/developerguide/iam-access-control.html)
- [CDK Best Practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)