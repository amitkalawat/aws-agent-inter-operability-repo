#!/bin/bash

# Test ACME Telemetry Pipeline
# Usage: ./test_pipeline.sh

set -e

echo "🧪 Testing ACME Telemetry Pipeline..."

# Configuration
REGION="us-west-2"
S3_BUCKET="acme-telemetry-878687028155-us-west-2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test telemetry generation
echo -e "${YELLOW}1. Testing Telemetry Generator Lambda...${NC}"
aws lambda invoke \
    --function-name AcmeTelemetry-Generator \
    --payload '{"test": true, "batch_size": 100}' \
    --cli-binary-format raw-in-base64-out \
    /tmp/test-output.json \
    --region ${REGION} > /dev/null 2>&1

RESULT=$(cat /tmp/test-output.json | jq -r '.statusCode')
if [ "$RESULT" == "200" ]; then
    VIEWER_COUNT=$(cat /tmp/test-output.json | jq -r '.body' | jq -r '.viewer_count')
    echo -e "${GREEN}✅ Generator working - Generated ${VIEWER_COUNT} events${NC}"
else
    echo -e "${RED}❌ Generator failed${NC}"
    cat /tmp/test-output.json
    exit 1
fi

# Check recent Lambda logs
echo -e "${YELLOW}2. Checking Producer Lambda logs...${NC}"
PRODUCER_LOGS=$(aws logs tail /aws/lambda/AcmeTelemetry-Producer --since 2m --format short --region ${REGION} 2>/dev/null | grep -c "Successfully sent" || echo "0")
if [ "$PRODUCER_LOGS" -gt "0" ]; then
    echo -e "${GREEN}✅ Producer successfully sending to MSK${NC}"
else
    echo -e "${YELLOW}⚠️  No recent producer activity (this is okay if just deployed)${NC}"
fi

# Check Firehose status
echo -e "${YELLOW}3. Checking Firehose status...${NC}"
FIREHOSE_STATUS=$(aws firehose describe-delivery-stream \
    --delivery-stream-name AcmeTelemetry-MSK-to-S3 \
    --query 'DeliveryStreamDescription.DeliveryStreamStatus' \
    --output text \
    --region ${REGION} 2>/dev/null || echo "NOT_FOUND")

if [ "$FIREHOSE_STATUS" == "ACTIVE" ]; then
    echo -e "${GREEN}✅ Firehose is ACTIVE${NC}"
elif [ "$FIREHOSE_STATUS" == "NOT_FOUND" ]; then
    echo -e "${RED}❌ Firehose not found - run ./scripts/create_firehose.sh${NC}"
else
    echo -e "${YELLOW}⚠️  Firehose status: ${FIREHOSE_STATUS}${NC}"
fi

# Check EventBridge rule
echo -e "${YELLOW}4. Checking EventBridge schedule...${NC}"
RULE_STATE=$(aws events describe-rule \
    --name AcmeTelemetry-GeneratorSchedule \
    --query 'State' \
    --output text \
    --region ${REGION} 2>/dev/null || echo "NOT_FOUND")

if [ "$RULE_STATE" == "ENABLED" ]; then
    echo -e "${GREEN}✅ EventBridge schedule is ENABLED (every 5 minutes)${NC}"
elif [ "$RULE_STATE" == "NOT_FOUND" ]; then
    echo -e "${RED}❌ EventBridge rule not found - run ./scripts/setup_eventbridge.sh${NC}"
else
    echo -e "${YELLOW}⚠️  EventBridge rule state: ${RULE_STATE}${NC}"
fi

# Check S3 for data
echo -e "${YELLOW}5. Checking S3 for data...${NC}"
FILE_COUNT=$(aws s3 ls s3://${S3_BUCKET}/telemetry/ --recursive --region ${REGION} 2>/dev/null | wc -l || echo "0")

if [ "$FILE_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✅ Found ${FILE_COUNT} files in S3${NC}"
    
    # Show recent files
    echo -e "${BLUE}Recent files:${NC}"
    aws s3 ls s3://${S3_BUCKET}/telemetry/ --recursive --region ${REGION} | tail -5
else
    echo -e "${YELLOW}⚠️  No data in S3 yet (wait 5 minutes for Firehose buffer)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Pipeline test complete!${NC}"
echo ""
echo "Summary:"
echo "--------"
echo "• Generator Lambda: ✅"
echo "• Producer Lambda: ${PRODUCER_LOGS:-0} recent sends"
echo "• Firehose: ${FIREHOSE_STATUS}"
echo "• EventBridge: ${RULE_STATE}"
echo "• S3 Data Files: ${FILE_COUNT}"
echo ""
echo "💡 Tips:"
echo "• Data appears in S3 after 5 minutes (Firehose buffer time)"
echo "• Run this script again in 5 minutes to see data in S3"
echo "• Check CloudWatch Logs for detailed debugging"

# Clean up
rm -f /tmp/test-output.json