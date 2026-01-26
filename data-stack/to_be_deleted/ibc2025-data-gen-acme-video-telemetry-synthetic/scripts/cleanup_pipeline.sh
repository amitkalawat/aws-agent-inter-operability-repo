#!/bin/bash

# ACME Telemetry Pipeline - Complete Cleanup Script
# WARNING: This script will DELETE all pipeline resources!
# Usage: ./cleanup_pipeline.sh [--force]

set -e

echo "⚠️  ACME Telemetry Pipeline - Cleanup Script"
echo "============================================"
echo ""
echo "WARNING: This script will DELETE the following resources:"
echo "  • Lambda functions (Generator, Producer)"
echo "  • EventBridge rules"
echo "  • Kinesis Data Firehose delivery stream"
echo "  • CloudWatch log groups"
echo "  • S3 data (optional)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="us-west-2"
S3_BUCKET="acme-telemetry-878687028155-us-west-2"
KEEP_S3_DATA=true  # Set to false to delete S3 data

# Parse arguments
FORCE_MODE=false
if [ "$1" == "--force" ]; then
    FORCE_MODE=true
fi

# Function to check if resource exists
resource_exists() {
    local resource_type=$1
    local resource_name=$2
    
    case $resource_type in
        "lambda")
            aws lambda get-function --function-name "$resource_name" --region "$REGION" >/dev/null 2>&1
            ;;
        "eventbridge")
            aws events describe-rule --name "$resource_name" --region "$REGION" >/dev/null 2>&1
            ;;
        "firehose")
            aws firehose describe-delivery-stream --delivery-stream-name "$resource_name" --region "$REGION" >/dev/null 2>&1
            ;;
        "loggroup")
            aws logs describe-log-groups --log-group-name-prefix "$resource_name" --region "$REGION" --query 'logGroups[0]' >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to delete resource with confirmation
delete_resource() {
    local resource_type=$1
    local resource_name=$2
    local description=$3
    
    echo -e "${YELLOW}Checking $description...${NC}"
    
    if resource_exists "$resource_type" "$resource_name"; then
        echo -e "${BLUE}  Found: $resource_name${NC}"
        
        if [ "$FORCE_MODE" = false ]; then
            read -p "  Delete $description? (y/n) " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}  Skipped${NC}"
                return 0
            fi
        fi
        
        case $resource_type in
            "lambda")
                echo -e "${RED}  Deleting Lambda function: $resource_name${NC}"
                aws lambda delete-function --function-name "$resource_name" --region "$REGION" 2>/dev/null || true
                ;;
            "eventbridge")
                # Remove targets first
                echo -e "${RED}  Removing EventBridge targets...${NC}"
                aws events remove-targets --rule "$resource_name" --ids "1" --region "$REGION" 2>/dev/null || true
                
                # Then delete rule
                echo -e "${RED}  Deleting EventBridge rule: $resource_name${NC}"
                aws events delete-rule --name "$resource_name" --region "$REGION" 2>/dev/null || true
                ;;
            "firehose")
                echo -e "${RED}  Deleting Firehose delivery stream: $resource_name${NC}"
                aws firehose delete-delivery-stream --delivery-stream-name "$resource_name" --region "$REGION" 2>/dev/null || true
                ;;
            "loggroup")
                echo -e "${RED}  Deleting CloudWatch log group: $resource_name${NC}"
                aws logs delete-log-group --log-group-name "$resource_name" --region "$REGION" 2>/dev/null || true
                ;;
        esac
        
        echo -e "${GREEN}  ✓ Deleted${NC}"
    else
        echo -e "${YELLOW}  Not found: $resource_name (skipping)${NC}"
    fi
}

# Confirmation prompt
if [ "$FORCE_MODE" = false ]; then
    echo -e "${RED}⚠️  This action cannot be undone!${NC}"
    read -p "Are you sure you want to proceed? Type 'yes' to confirm: " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Cleanup cancelled.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}Starting cleanup...${NC}"
echo ""

# 1. Disable EventBridge Rule first (to stop triggering Lambda)
echo -e "${BLUE}═══ Step 1: Disabling EventBridge Rule ═══${NC}"
if resource_exists "eventbridge" "AcmeTelemetry-GeneratorSchedule"; then
    echo -e "${YELLOW}Disabling EventBridge rule...${NC}"
    aws events disable-rule --name "AcmeTelemetry-GeneratorSchedule" --region "$REGION" 2>/dev/null || true
    echo -e "${GREEN}✓ Rule disabled${NC}"
fi

# 2. Delete EventBridge Rule
echo ""
echo -e "${BLUE}═══ Step 2: Deleting EventBridge Rule ═══${NC}"
delete_resource "eventbridge" "AcmeTelemetry-GeneratorSchedule" "EventBridge scheduled rule"

# 3. Delete Lambda Functions
echo ""
echo -e "${BLUE}═══ Step 3: Deleting Lambda Functions ═══${NC}"
delete_resource "lambda" "AcmeTelemetry-Generator" "Generator Lambda function"
delete_resource "lambda" "AcmeTelemetry-Producer" "Producer Lambda function"

# Also check for other Lambda functions that might have been created
delete_resource "lambda" "AcmeTelemetry-TopicManager" "Topic Manager Lambda function"
delete_resource "lambda" "AcmeTelemetry-ConnectivityTest" "Connectivity Test Lambda function"
delete_resource "lambda" "AcmeTelemetry-KafkaAdminTest" "Kafka Admin Test Lambda function"

# 4. Delete Kinesis Data Firehose
echo ""
echo -e "${BLUE}═══ Step 4: Deleting Kinesis Data Firehose ═══${NC}"
delete_resource "firehose" "AcmeTelemetry-MSK-to-S3" "Firehose delivery stream"

# 5. Delete CloudWatch Log Groups
echo ""
echo -e "${BLUE}═══ Step 5: Deleting CloudWatch Log Groups ═══${NC}"
delete_resource "loggroup" "/aws/lambda/AcmeTelemetry-Generator" "Generator Lambda log group"
delete_resource "loggroup" "/aws/lambda/AcmeTelemetry-Producer" "Producer Lambda log group"
delete_resource "loggroup" "/aws/lambda/AcmeTelemetry-TopicManager" "Topic Manager log group"
delete_resource "loggroup" "/aws/kinesisfirehose/AcmeTelemetry-MSK-to-S3" "Firehose log group"

# 6. Optional: Clean S3 Data
echo ""
echo -e "${BLUE}═══ Step 6: S3 Data ═══${NC}"
if [ "$KEEP_S3_DATA" = true ]; then
    echo -e "${YELLOW}S3 data preserved in: s3://${S3_BUCKET}/telemetry/${NC}"
    echo -e "${YELLOW}To delete manually: aws s3 rm s3://${S3_BUCKET}/telemetry/ --recursive${NC}"
else
    if [ "$FORCE_MODE" = false ]; then
        read -p "Delete all telemetry data from S3? This is PERMANENT! (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Deleting S3 data...${NC}"
            aws s3 rm "s3://${S3_BUCKET}/telemetry/" --recursive --region "$REGION"
            aws s3 rm "s3://${S3_BUCKET}/errors/" --recursive --region "$REGION" 2>/dev/null || true
            echo -e "${GREEN}✓ S3 data deleted${NC}"
        else
            echo -e "${YELLOW}S3 data preserved${NC}"
        fi
    fi
fi

# 7. List remaining resources (informational)
echo ""
echo -e "${BLUE}═══ Step 7: Resource Check ═══${NC}"
echo -e "${YELLOW}Resources that must be cleaned up separately:${NC}"
echo "  • MSK Cluster (not deleted by this script)"
echo "  • MSK topic 'acme-telemetry' (use Kafka admin tools)"
echo "  • IAM Roles (if created manually)"
echo "  • VPC/Security Groups (if created manually)"
echo "  • S3 Bucket itself (if you want to delete it)"

# 8. Final check for remaining Lambda functions
echo ""
echo -e "${BLUE}═══ Final Check ═══${NC}"
REMAINING_LAMBDAS=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'AcmeTelemetry')].FunctionName" --output text --region "$REGION" 2>/dev/null)

if [ -n "$REMAINING_LAMBDAS" ]; then
    echo -e "${YELLOW}⚠️  Found remaining Lambda functions:${NC}"
    echo "$REMAINING_LAMBDAS"
    echo -e "${YELLOW}Run with --force to delete all, or delete manually${NC}"
else
    echo -e "${GREEN}✓ No AcmeTelemetry Lambda functions found${NC}"
fi

# Check for remaining Firehose streams
REMAINING_FIREHOSE=$(aws firehose list-delivery-streams --query "DeliveryStreamNames[?contains(@, 'AcmeTelemetry')]" --output text --region "$REGION" 2>/dev/null)

if [ -n "$REMAINING_FIREHOSE" ]; then
    echo -e "${YELLOW}⚠️  Found remaining Firehose streams:${NC}"
    echo "$REMAINING_FIREHOSE"
else
    echo -e "${GREEN}✓ No AcmeTelemetry Firehose streams found${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Cleanup process completed!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "Summary:"
echo "  • EventBridge rules: Deleted"
echo "  • Lambda functions: Deleted"
echo "  • Firehose streams: Deleted"
echo "  • CloudWatch logs: Deleted"
if [ "$KEEP_S3_DATA" = true ]; then
    echo "  • S3 data: PRESERVED"
else
    echo "  • S3 data: Deleted"
fi
echo ""
echo -e "${YELLOW}Note: MSK cluster and topic must be managed separately${NC}"