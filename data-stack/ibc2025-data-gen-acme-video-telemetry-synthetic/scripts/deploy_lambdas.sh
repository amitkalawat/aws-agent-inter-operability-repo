#!/bin/bash

# Deploy Lambda Functions for ACME Telemetry Pipeline
# Usage: ./deploy_lambdas.sh

set -e

echo "🚀 Deploying ACME Telemetry Lambda Functions..."

# Configuration
REGION="eu-central-1"
ACCOUNT_ID="241533163649"
VPC_SUBNET_IDS="subnet-0647a0a20b64e92cd,subnet-0be036fae34308206,subnet-09babfb5a5e21493c"
SECURITY_GROUP_ID="sg-0ffdd5b145ba72b7c"
MSK_CLUSTER_ARN="arn:aws:kafka:eu-central-1:241533163649:cluster/simple-msk-eu-central-1/26147c0d-2edc-4f80-9428-346a44b1659e-2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if Lambda exists
function_exists() {
    aws lambda get-function --function-name $1 --region $REGION >/dev/null 2>&1
}

# Deploy Generator Lambda
echo -e "${YELLOW}📦 Packaging Telemetry Generator...${NC}"
cd lambda/telemetry_generator
zip -r ../../generator.zip . -q
cd ../..

if function_exists "AcmeTelemetry-Generator"; then
    echo -e "${YELLOW}🔄 Updating Telemetry Generator...${NC}"
    aws lambda update-function-code \
        --function-name AcmeTelemetry-Generator \
        --zip-file fileb://generator.zip \
        --region $REGION > /dev/null
    
    aws lambda update-function-configuration \
        --function-name AcmeTelemetry-Generator \
        --environment Variables={MSK_PRODUCER_FUNCTION_NAME=AcmeTelemetry-Producer,DATA_LOADER_FUNCTION_NAME=AcmeTelemetry-DataLoader} \
        --timeout 300 \
        --memory-size 1024 \
        --region $REGION > /dev/null
else
    echo -e "${GREEN}✨ Creating Telemetry Generator...${NC}"
    aws lambda create-function \
        --function-name AcmeTelemetry-Generator \
        --runtime python3.9 \
        --role arn:aws:iam::${ACCOUNT_ID}:role/AcmeTelemetry-Generator-Role \
        --handler handler.lambda_handler \
        --zip-file fileb://generator.zip \
        --timeout 300 \
        --memory-size 1024 \
        --environment Variables={MSK_PRODUCER_FUNCTION_NAME=AcmeTelemetry-Producer,DATA_LOADER_FUNCTION_NAME=AcmeTelemetry-DataLoader} \
        --region $REGION > /dev/null
fi

echo -e "${GREEN}✅ Telemetry Generator deployed${NC}"

# Deploy Producer Lambda
echo -e "${YELLOW}📦 Packaging MSK Producer...${NC}"
cd lambda/msk_producer

# Install dependencies
pip install -r requirements.txt -t . -q

zip -r ../../producer.zip . -q
cd ../..

if function_exists "AcmeTelemetry-Producer"; then
    echo -e "${YELLOW}🔄 Updating MSK Producer...${NC}"
    aws lambda update-function-code \
        --function-name AcmeTelemetry-Producer \
        --zip-file fileb://producer.zip \
        --region $REGION > /dev/null
    
    aws lambda update-function-configuration \
        --function-name AcmeTelemetry-Producer \
        --vpc-config SubnetIds=${VPC_SUBNET_IDS},SecurityGroupIds=${SECURITY_GROUP_ID} \
        --environment Variables={MSK_CLUSTER_ARN=${MSK_CLUSTER_ARN},TOPIC_NAME=acme-telemetry} \
        --timeout 60 \
        --memory-size 512 \
        --region $REGION > /dev/null
else
    echo -e "${GREEN}✨ Creating MSK Producer...${NC}"
    aws lambda create-function \
        --function-name AcmeTelemetry-Producer \
        --runtime python3.9 \
        --role arn:aws:iam::${ACCOUNT_ID}:role/AcmeTelemetry-Producer-Role \
        --handler handler.lambda_handler \
        --zip-file fileb://producer.zip \
        --timeout 60 \
        --memory-size 512 \
        --vpc-config SubnetIds=${VPC_SUBNET_IDS},SecurityGroupIds=${SECURITY_GROUP_ID} \
        --environment Variables={MSK_CLUSTER_ARN=${MSK_CLUSTER_ARN},TOPIC_NAME=acme-telemetry} \
        --region $REGION > /dev/null
fi

echo -e "${GREEN}✅ MSK Producer deployed${NC}"

# Deploy Data Loader Lambda
echo -e "${YELLOW}📦 Packaging Data Loader...${NC}"
cd lambda/data_loader
zip -r ../../data-loader.zip . -q
cd ../..

if function_exists "AcmeTelemetry-DataLoader"; then
    echo -e "${YELLOW}🔄 Updating Data Loader...${NC}"
    aws lambda update-function-code \
        --function-name AcmeTelemetry-DataLoader \
        --zip-file fileb://data-loader.zip \
        --region $REGION > /dev/null
    
    aws lambda update-function-configuration \
        --function-name AcmeTelemetry-DataLoader \
        --timeout 60 \
        --memory-size 512 \
        --region $REGION > /dev/null
else
    echo -e "${GREEN}✨ Creating Data Loader...${NC}"
    aws lambda create-function \
        --function-name AcmeTelemetry-DataLoader \
        --runtime python3.9 \
        --role arn:aws:iam::${ACCOUNT_ID}:role/AcmeTelemetry-DataLoader-Role \
        --handler handler.lambda_handler \
        --zip-file fileb://data-loader.zip \
        --timeout 60 \
        --memory-size 512 \
        --region $REGION > /dev/null
fi

echo -e "${GREEN}✅ Data Loader deployed${NC}"

# Clean up zip files
rm -f generator.zip producer.zip data-loader.zip

echo -e "${GREEN}🎉 Lambda functions deployed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Run: python scripts/create_msk_topic.py"
echo "2. Run: ./scripts/setup_eventbridge.sh"
echo "3. Run: ./scripts/create_firehose.sh"