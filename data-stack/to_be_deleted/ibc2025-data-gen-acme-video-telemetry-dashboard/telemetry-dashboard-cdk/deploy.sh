#!/bin/bash

# Deployment script for Telemetry Dashboard CDK Stack
# Update these values with your actual AWS infrastructure details

# Set AWS region (found from outputs.json)
export CDK_DEFAULT_REGION="eu-central-1"

# VPC Configuration (from cdk.context.json)
export VPC_ID="vpc-05ef4d2808525f6a2"
export PRIVATE_SUBNET_IDS="subnet-0be036fae34308206,subnet-09babfb5a5e21493c,subnet-0647a0a20b64e92cd"

# MSK Configuration
export MSK_CLUSTER_ARN="arn:aws:kafka:eu-central-1:241533163649:cluster/simple-msk-eu-central-1/26147c0d-2edc-4f80-9428-346a44b1659e-2"

# Security group for MSK access
export MSK_SECURITY_GROUP_ID="sg-0ffdd5b145ba72b7c"


echo "Deploying with configuration:"
echo "  Region: $CDK_DEFAULT_REGION"
echo "  VPC: $VPC_ID"
echo "  Subnets: $PRIVATE_SUBNET_IDS"
echo "  MSK Cluster: $MSK_CLUSTER_ARN"
echo "  Security Group: $MSK_SECURITY_GROUP_ID"
echo ""

# Deploy the stack
npm run deploy