# ACME Telemetry Pipeline - CDK Implementation

This directory contains the AWS CDK (Cloud Development Kit) implementation of the ACME Telemetry Pipeline. CDK allows you to define cloud infrastructure using Python code.

## 📁 Directory Structure

```
cdk/
├── app.py                      # Main CDK application entry point
├── app_complete.py            # Complete app with all stacks
├── cdk.json                   # CDK configuration
├── cdk.context.json           # Environment-specific configuration
├── requirements.txt           # Python dependencies
├── deploy.sh                  # Deployment script
├── stacks/
│   ├── __init__.py
│   ├── telemetry_pipeline_stack.py  # Main pipeline stack
│   ├── networking_stack.py          # VPC and networking (optional)
│   ├── msk_stack.py                 # MSK cluster (optional)
│   └── monitoring_stack.py          # CloudWatch dashboards and alarms
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Python 3.9+** installed
3. **Node.js** (for CDK CLI)
4. **Existing MSK Cluster** (or deploy one using the MSK stack)

### Installation

1. Install AWS CDK globally:
```bash
npm install -g aws-cdk
```

2. Create Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

Edit `cdk.context.json` with your environment details:

```json
{
  "vpc_id": "vpc-xxxxx",                    # Your VPC ID (leave empty to create new)
  "msk_cluster_arn": "arn:aws:kafka:...",   # Your MSK cluster ARN (required)
  "s3_bucket_name": "your-bucket",          # S3 bucket (leave empty to create new)
  "deploy_networking": false,               # Set true to deploy VPC
  "deploy_msk": false,                      # Set true to deploy MSK cluster
  "deploy_monitoring": true,                # Set true for monitoring stack
  "alert_email": "your-email@example.com"   # Email for alerts
}
```

### Deployment

#### Option 1: Using the deployment script (Recommended)
```bash
chmod +x deploy.sh
./deploy.sh
```

#### Option 2: Manual deployment
```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Synthesize CloudFormation template
cdk synth

# Deploy all stacks
cdk deploy --all

# Or deploy specific stacks
cdk deploy AcmeTelemetry-Pipeline
cdk deploy AcmeTelemetry-Monitoring
```

## 📚 Stack Details

### 1. Telemetry Pipeline Stack (`telemetry_pipeline_stack.py`)

Main stack containing:
- **Lambda Functions**:
  - `AcmeTelemetry-Generator`: Generates telemetry events
  - `AcmeTelemetry-Producer`: Sends events to MSK
- **EventBridge Rule**: Triggers generation every 5 minutes
- **Kinesis Data Firehose**: Delivers data from MSK to S3
- **IAM Roles**: Necessary permissions for all components
- **Security Groups**: Network access controls

### 2. Networking Stack (`networking_stack.py`)

Optional stack for VPC creation:
- **VPC**: Multi-AZ VPC with public/private subnets
- **NAT Gateway**: For Lambda internet access
- **VPC Endpoints**: Cost optimization for AWS services

### 3. MSK Stack (`msk_stack.py`)

Optional stack for MSK cluster:
- **MSK Cluster**: 3-node Kafka cluster
- **Security Groups**: MSK access controls
- **Configuration**: Kafka settings
- **CloudWatch Logs**: Cluster logging

### 4. Monitoring Stack (`monitoring_stack.py`)

Observability components:
- **CloudWatch Dashboard**: Real-time metrics visualization
- **CloudWatch Alarms**: Error and performance alerts
- **SNS Topic**: Alert notifications

## 🔧 Common Operations

### Update Lambda code
```bash
# After modifying Lambda code in ../lambda/
cdk deploy AcmeTelemetry-Pipeline
```

### Update monitoring
```bash
cdk deploy AcmeTelemetry-Monitoring
```

### Destroy stacks
```bash
# Remove all stacks (BE CAREFUL!)
cdk destroy --all

# Or specific stack
cdk destroy AcmeTelemetry-Monitoring
```

### View stack outputs
```bash
cdk deploy --outputs-file outputs.json
cat outputs.json
```

## 📊 Configuration Options

### Using Existing Resources

If you have existing AWS resources:

1. **Existing VPC**:
   - Set `vpc_id` in `cdk.context.json`
   - Set `deploy_networking` to `false`

2. **Existing MSK Cluster**:
   - Set `msk_cluster_arn` in `cdk.context.json`
   - Set `deploy_msk` to `false`

3. **Existing S3 Bucket**:
   - Set `s3_bucket_name` in `cdk.context.json`

### Creating New Resources

Leave the respective fields empty and set deploy flags to `true`:

```json
{
  "vpc_id": "",
  "deploy_networking": true,
  "deploy_msk": true
}
```

## 🔍 Troubleshooting

### CDK Bootstrap Issues
```bash
# If bootstrap fails, try with explicit account/region
cdk bootstrap aws://ACCOUNT/REGION
```

### Python Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
pip install -r requirements.txt
```

### Stack Deployment Failures
```bash
# Check CloudFormation console for detailed errors
aws cloudformation describe-stack-events \
  --stack-name AcmeTelemetry-Pipeline \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

### MSK Connectivity Issues
- Ensure Lambda functions are in the same VPC as MSK
- Check security group rules allow port 9098
- Verify MSK cluster has IAM authentication enabled

## 🏷️ Cost Optimization

### Tips to reduce costs:
1. Use single NAT Gateway (configured by default)
2. Enable VPC endpoints for AWS services
3. Use smaller MSK instance types for dev/test
4. Set appropriate CloudWatch log retention
5. Configure S3 lifecycle policies

## 📈 Monitoring

After deployment, access:
- **CloudWatch Dashboard**: Check stack outputs for URL
- **S3 Data**: `s3://your-bucket/telemetry/`
- **Lambda Logs**: CloudWatch Logs console
- **Firehose Metrics**: CloudWatch Metrics

## 🔐 Security Best Practices

1. **IAM Roles**: Least privilege principle applied
2. **Encryption**: Data encrypted in transit and at rest
3. **VPC**: Private subnets for compute resources
4. **Security Groups**: Restrictive inbound rules
5. **MSK**: IAM authentication enabled

## 📝 Environment Variables

Set these before deployment:
```bash
export CDK_DEFAULT_ACCOUNT=123456789012
export CDK_DEFAULT_REGION=us-west-2
```

## 🆘 Support

For issues or questions:
1. Check the [main documentation](../docs/)
2. Review CloudFormation events in AWS Console
3. Check CloudWatch Logs for Lambda errors
4. Verify all prerequisites are met

## 📄 License

Copyright 2025 ACME Corporation. All rights reserved.