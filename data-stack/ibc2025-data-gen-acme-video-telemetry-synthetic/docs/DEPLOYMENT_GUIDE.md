# ACME Telemetry Pipeline - Complete Deployment Guide

## Overview
Real-time telemetry generation system for ACME streaming platform using AWS services to generate, process, and store viewing telemetry data.

## Architecture Components

### AWS Services Used
- **EventBridge**: Scheduled rule triggering every 5 minutes
- **Lambda Functions**: 
  - `AcmeTelemetry-Generator`: Generates telemetry events
  - `AcmeTelemetry-Producer`: Sends events to MSK
- **Amazon MSK**: Kafka cluster for event streaming
- **Kinesis Data Firehose**: Consumes from MSK and delivers to S3
- **S3**: Data lake storage for telemetry data

## Prerequisites

### Required AWS Resources
- MSK Cluster: `simple-msk-us-west-2` (ARN: `arn:aws:kafka:us-west-2:878687028155:cluster/simple-msk-us-west-2/05a8cbf7-ea44-42d5-a3ca-2d78cc557cc5-6`)
- VPC: `llamaindex-vpc` with private subnets
- S3 Bucket: `acme-telemetry-878687028155-us-west-2`
- NAT Gateway for Lambda internet access

## Deployment Steps

### 1. Deploy Lambda Functions

#### Generator Lambda
```bash
# Create deployment package
cd lambda/telemetry_generator
zip -r ../generator.zip .
cd ../..

# Create Lambda function
aws lambda create-function \
  --function-name AcmeTelemetry-Generator \
  --runtime python3.9 \
  --role arn:aws:iam::878687028155:role/AcmeTelemetry-Generator-Role \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda/generator.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables={MSK_PRODUCER_FUNCTION_NAME=AcmeTelemetry-Producer}
```

#### Producer Lambda
```bash
# Create deployment package with dependencies
cd lambda/msk_producer
pip install -r requirements.txt -t .
zip -r ../producer.zip .
cd ../..

# Create Lambda function
aws lambda create-function \
  --function-name AcmeTelemetry-Producer \
  --runtime python3.9 \
  --role arn:aws:iam::878687028155:role/AcmeTelemetry-Producer-Role \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda/producer.zip \
  --timeout 60 \
  --memory-size 512 \
  --vpc-config SubnetIds=subnet-00b2bc68a08c8eb53,subnet-0aeb965033e0bc1b4,subnet-0d68c58e5d45f6e48,SecurityGroupIds=sg-093aa8f84f27c5c06 \
  --environment Variables={MSK_CLUSTER_ARN=arn:aws:kafka:us-west-2:878687028155:cluster/simple-msk-us-west-2/05a8cbf7-ea44-42d5-a3ca-2d78cc557cc5-6,TOPIC_NAME=acme-telemetry}
```

### 2. Create MSK Topic

The topic must be created before Firehose can consume from it:

```python
# Use the create_topic.py script or this command via Lambda
aws lambda invoke --function-name AcmeTelemetry-TopicManager \
  --payload '{"action": "create_topic"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/topic-result.json
```

### 3. Configure MSK Cluster Policy

Enable Firehose to create VPC connections to MSK:

```bash
# Apply cluster policy
aws kafka put-cluster-policy \
  --cluster-arn "arn:aws:kafka:us-west-2:878687028155:cluster/simple-msk-us-west-2/05a8cbf7-ea44-42d5-a3ca-2d78cc557cc5-6" \
  --policy file:///tmp/msk-cluster-policy.json
```

Policy content:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "firehose.amazonaws.com"
    },
    "Action": [
      "kafka:CreateVpcConnection",
      "kafka:GetBootstrapBrokers",
      "kafka:DescribeCluster",
      "kafka:DescribeClusterV2",
      "kafka-cluster:Connect",
      "kafka-cluster:DescribeCluster",
      "kafka-cluster:ReadData",
      "kafka-cluster:DescribeGroup",
      "kafka-cluster:AlterGroup",
      "kafka-cluster:DescribeTopic"
    ],
    "Resource": "*",
    "Condition": {
      "StringEquals": {
        "aws:SourceAccount": "878687028155"
      }
    }
  }]
}
```

### 4. Create Kinesis Data Firehose

```bash
aws firehose create-delivery-stream \
  --delivery-stream-name AcmeTelemetry-MSK-to-S3 \
  --delivery-stream-type MSKAsSource \
  --cli-input-json file:///tmp/firehose-config.json
```

Firehose configuration:
```json
{
  "MSKSourceConfiguration": {
    "MSKClusterARN": "arn:aws:kafka:us-west-2:878687028155:cluster/simple-msk-us-west-2/05a8cbf7-ea44-42d5-a3ca-2d78cc557cc5-6",
    "TopicName": "acme-telemetry",
    "AuthenticationConfiguration": {
      "RoleARN": "arn:aws:iam::878687028155:role/AcmeTelemetry-Firehose-Role",
      "Connectivity": "PRIVATE"
    }
  },
  "ExtendedS3DestinationConfiguration": {
    "BucketARN": "arn:aws:s3:::acme-telemetry-878687028155-us-west-2",
    "Prefix": "telemetry/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/",
    "ErrorOutputPrefix": "errors/!{firehose:error-output-type}/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
    "BufferingHints": {
      "SizeInMBs": 128,
      "IntervalInSeconds": 300
    },
    "CompressionFormat": "GZIP",
    "RoleARN": "arn:aws:iam::878687028155:role/AcmeTelemetry-Firehose-Role"
  }
}
```

### 5. Create EventBridge Rule

```bash
# Create scheduled rule
aws events put-rule \
  --name AcmeTelemetry-GeneratorSchedule \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

# Add Lambda target
aws events put-targets \
  --rule AcmeTelemetry-GeneratorSchedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-west-2:878687028155:function:AcmeTelemetry-Generator"

# Grant permission to EventBridge
aws lambda add-permission \
  --function-name AcmeTelemetry-Generator \
  --statement-id AllowEventBridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-west-2:878687028155:rule/AcmeTelemetry-GeneratorSchedule
```

## IAM Roles Required

### Generator Lambda Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-west-2:878687028155:function:AcmeTelemetry-Producer"
    }
  ]
}
```

### Producer Lambda Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kafka:GetBootstrapBrokers",
        "kafka:DescribeCluster",
        "kafka-cluster:Connect",
        "kafka-cluster:AlterCluster",
        "kafka-cluster:DescribeCluster",
        "kafka-cluster:WriteData",
        "kafka-cluster:DescribeTopic",
        "kafka-cluster:AlterTopic",
        "kafka-cluster:CreateTopic"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:AssignPrivateIpAddresses",
        "ec2:UnassignPrivateIpAddresses"
      ],
      "Resource": "*"
    }
  ]
}
```

### Firehose Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::acme-telemetry-878687028155-us-west-2",
        "arn:aws:s3:::acme-telemetry-878687028155-us-west-2/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kafka:GetBootstrapBrokers",
        "kafka:DescribeCluster",
        "kafka:DescribeClusterV2",
        "kafka-cluster:Connect",
        "kafka-cluster:DescribeCluster",
        "kafka-cluster:ReadData",
        "kafka-cluster:DescribeGroup",
        "kafka-cluster:AlterGroup",
        "kafka-cluster:DescribeTopic"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVpcs",
        "ec2:DescribeVpcAttribute",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "ec2:CreateNetworkInterface",
        "ec2:CreateNetworkInterfacePermission",
        "ec2:DeleteNetworkInterface"
      ],
      "Resource": "*"
    }
  ]
}
```

## Critical Configuration Points

### 1. MSK IAM Authentication
- Must use `SASL_SSL` security protocol
- Mechanism: `OAUTHBEARER`
- Token provider must use `aws-msk-iam-sasl-signer`

### 2. VPC Configuration
- Lambda functions MUST be in the same VPC as MSK
- Security group must allow:
  - Port 9098 for MSK IAM auth
  - Outbound HTTPS for AWS API calls

### 3. Firehose Buffer Settings
- Default: 5 minutes or 128MB
- Data won't appear in S3 until buffer conditions are met

### 4. Topic Creation
- MUST create topic before Firehose starts consuming
- Configuration:
  - Partitions: 20
  - Replication factor: 3
  - Retention: 7 days

## Troubleshooting

### Common Issues and Solutions

1. **Lambda Timeout when connecting to MSK**
   - Ensure Lambda is in VPC with MSK
   - Check security group allows port 9098
   - Verify MSK cluster has IAM auth enabled

2. **Firehose not consuming data**
   - Verify topic exists before creating Firehose
   - Check MSK cluster policy allows Firehose
   - Ensure Firehose IAM role has correct permissions

3. **No data in S3**
   - Wait for buffer time (5 minutes) or size (128MB)
   - Check Firehose error logs
   - Verify S3 bucket permissions

4. **Producer Lambda environment variable error**
   - Set `MSK_PRODUCER_FUNCTION_NAME=AcmeTelemetry-Producer` in Generator Lambda

## Monitoring

### CloudWatch Metrics
- Lambda invocations and errors
- Firehose IncomingRecords
- S3 bucket size

### Logs
- `/aws/lambda/AcmeTelemetry-Generator`
- `/aws/lambda/AcmeTelemetry-Producer`
- Check S3 errors folder for Firehose failures

## Data Output

Data is stored in S3 with:
- Partitioning: `year/month/day/hour`
- Format: GZIP compressed JSON
- Fields: All 24 telemetry schema fields
- Naming: `AcmeTelemetry-MSK-to-S3-{partition}-{timestamp}-{uuid}.gz`