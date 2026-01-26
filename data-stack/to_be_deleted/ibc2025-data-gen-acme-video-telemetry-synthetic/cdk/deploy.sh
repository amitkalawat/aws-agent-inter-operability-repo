#!/bin/bash

# ACME Telemetry Pipeline CDK Deployment Script

set -e

echo "🚀 ACME Telemetry Pipeline CDK Deployment"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI.${NC}"
    exit 1
fi

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo -e "${YELLOW}⚠️  CDK not found. Installing...${NC}"
    npm install -g aws-cdk
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.${NC}"
    exit 1
fi

# Setup Python virtual environment
echo -e "${YELLOW}Setting up Python environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt -q

# Bootstrap CDK (if needed)
echo -e "${YELLOW}Checking CDK bootstrap...${NC}"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)

if [ -z "$REGION" ]; then
    REGION="us-west-2"
fi

cdk bootstrap aws://${ACCOUNT}/${REGION} 2>/dev/null || true

# Configuration
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "Account: ${ACCOUNT}"
echo "Region: ${REGION}"

# Read configuration
VPC_ID=$(grep vpc_id cdk.context.json | cut -d'"' -f4)
MSK_ARN=$(grep msk_cluster_arn cdk.context.json | cut -d'"' -f4)

if [ -z "$VPC_ID" ]; then
    echo -e "${YELLOW}No VPC ID provided. Will create new VPC.${NC}"
else
    echo "VPC ID: ${VPC_ID}"
fi

if [ -z "$MSK_ARN" ]; then
    echo -e "${RED}❌ MSK Cluster ARN is required!${NC}"
    echo "Please update cdk.context.json with your MSK cluster ARN"
    exit 1
else
    echo "MSK Cluster: ${MSK_ARN:0:50}..."
fi

# Synthesize
echo ""
echo -e "${YELLOW}Synthesizing CDK app...${NC}"
cdk synth

# Deploy
echo ""
echo -e "${GREEN}Ready to deploy!${NC}"
read -p "Do you want to deploy now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deploying stacks...${NC}"
    
    # Deploy main pipeline stack
    cdk deploy AcmeTelemetry-Pipeline --require-approval never
    
    # Check if monitoring should be deployed
    MONITORING=$(grep deploy_monitoring cdk.context.json | cut -d':' -f2 | tr -d ' ,' | tr -d '"')
    if [ "$MONITORING" == "true" ]; then
        echo -e "${YELLOW}Deploying monitoring stack...${NC}"
        cdk deploy AcmeTelemetry-Monitoring --require-approval never
    fi
    
    echo ""
    echo -e "${GREEN}✅ Deployment complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Create MSK topic: python ../scripts/create_msk_topic.py"
    echo "2. Apply MSK cluster policy (check stack outputs)"
    echo "3. Test the pipeline: ../scripts/test_pipeline.sh"
    echo "4. Check CloudWatch dashboard"
else
    echo -e "${YELLOW}Deployment cancelled.${NC}"
fi

# Deactivate virtual environment
deactivate