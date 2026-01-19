#!/bin/bash

# Set up EventBridge Schedule for ACME Telemetry Pipeline
# Usage: ./setup_eventbridge.sh

set -e

echo "⏰ Setting up EventBridge Schedule..."

# Configuration
REGION="eu-central-1"
ACCOUNT_ID="241533163649"
RULE_NAME="AcmeTelemetry-GeneratorSchedule"
FUNCTION_NAME="AcmeTelemetry-Generator"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create or update the schedule rule
echo -e "${YELLOW}Creating schedule rule...${NC}"
aws events put-rule \
    --name ${RULE_NAME} \
    --schedule-expression "rate(5 minutes)" \
    --description "Trigger telemetry generation every 5 minutes" \
    --state ENABLED \
    --region ${REGION}

# Add Lambda target to the rule
echo -e "${YELLOW}Adding Lambda target...${NC}"
aws events put-targets \
    --rule ${RULE_NAME} \
    --targets "Id"="1","Arn"="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}" \
    --region ${REGION}

# Grant permission to EventBridge to invoke the Lambda
echo -e "${YELLOW}Granting invoke permission...${NC}"
aws lambda add-permission \
    --function-name ${FUNCTION_NAME} \
    --statement-id AllowEventBridge-${RULE_NAME} \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/${RULE_NAME} \
    --region ${REGION} 2>/dev/null || true

echo -e "${GREEN}✅ EventBridge schedule created successfully!${NC}"
echo ""
echo "The Lambda function will be triggered every 5 minutes."
echo "To check the rule status: aws events describe-rule --name ${RULE_NAME}"
echo "To disable: aws events disable-rule --name ${RULE_NAME}"
echo "To enable: aws events enable-rule --name ${RULE_NAME}"