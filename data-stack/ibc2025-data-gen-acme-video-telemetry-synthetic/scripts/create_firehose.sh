#!/bin/bash

# Create Kinesis Data Firehose for ACME Telemetry Pipeline
# Usage: ./create_firehose.sh

set -e

echo "🔥 Creating Kinesis Data Firehose Delivery Stream..."

# Configuration
REGION="eu-central-1"
ACCOUNT_ID="241533163649"
STREAM_NAME="AcmeTelemetry-MSK-to-S3"
CONFIG_FILE="config/firehose-config-frankfurt.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Check if MSK cluster policy is set
echo -e "${YELLOW}Checking MSK cluster policy...${NC}"
MSK_CLUSTER_ARN="arn:aws:kafka:eu-central-1:241533163649:cluster/simple-msk-eu-central-1/26147c0d-2edc-4f80-9428-346a44b1659e-2"

POLICY_EXISTS=$(aws kafka get-cluster-policy --cluster-arn ${MSK_CLUSTER_ARN} --region ${REGION} 2>/dev/null | jq -r '.Policy' || echo "null")

if [ "$POLICY_EXISTS" == "null" ]; then
    echo -e "${YELLOW}Setting MSK cluster policy...${NC}"
    aws kafka put-cluster-policy \
        --cluster-arn ${MSK_CLUSTER_ARN} \
        --policy file://config/msk-cluster-policy-frankfurt.json \
        --region ${REGION}
    echo -e "${GREEN}✅ MSK cluster policy set${NC}"
else
    echo -e "${GREEN}✅ MSK cluster policy already exists${NC}"
fi

# Check if delivery stream already exists
STREAM_EXISTS=$(aws firehose describe-delivery-stream --delivery-stream-name ${STREAM_NAME} --region ${REGION} 2>/dev/null | jq -r '.DeliveryStreamDescription.DeliveryStreamName' || echo "null")

if [ "$STREAM_EXISTS" != "null" ]; then
    echo -e "${YELLOW}⚠️  Delivery stream ${STREAM_NAME} already exists${NC}"
    read -p "Do you want to delete and recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deleting existing delivery stream...${NC}"
        aws firehose delete-delivery-stream \
            --delivery-stream-name ${STREAM_NAME} \
            --region ${REGION}
        
        # Wait for deletion
        echo -e "${YELLOW}Waiting for deletion to complete...${NC}"
        while true; do
            STATUS=$(aws firehose describe-delivery-stream --delivery-stream-name ${STREAM_NAME} --region ${REGION} 2>/dev/null | jq -r '.DeliveryStreamDescription.DeliveryStreamStatus' || echo "DELETED")
            if [ "$STATUS" == "DELETED" ]; then
                break
            fi
            echo -n "."
            sleep 5
        done
        echo ""
    else
        echo -e "${YELLOW}Skipping Firehose creation${NC}"
        exit 0
    fi
fi

# Create the delivery stream
echo -e "${YELLOW}Creating delivery stream...${NC}"
aws firehose create-delivery-stream \
    --cli-input-json file://${CONFIG_FILE} \
    --region ${REGION}

# Wait for creation
echo -e "${YELLOW}Waiting for delivery stream to become active...${NC}"
while true; do
    STATUS=$(aws firehose describe-delivery-stream --delivery-stream-name ${STREAM_NAME} --region ${REGION} 2>/dev/null | jq -r '.DeliveryStreamDescription.DeliveryStreamStatus' || echo "CREATING")
    if [ "$STATUS" == "ACTIVE" ]; then
        break
    fi
    echo -n "."
    sleep 5
done
echo ""

echo -e "${GREEN}✅ Firehose delivery stream created successfully!${NC}"
echo ""
echo "Stream Name: ${STREAM_NAME}"
echo "Status: ACTIVE"
echo ""
echo "Data will be delivered to S3 after:"
echo "- 5 minutes (buffer time) OR"
echo "- 128 MB of data (buffer size)"
echo ""
echo "To check status: aws firehose describe-delivery-stream --delivery-stream-name ${STREAM_NAME}"