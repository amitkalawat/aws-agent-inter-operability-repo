#!/bin/bash

# ACME Telemetry Pipeline - Resource Listing Script
# Lists all deployed pipeline resources
# Usage: ./list_resources.sh

set -e

echo "📋 ACME Telemetry Pipeline - Resource Status"
echo "============================================"
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

# Function to check resource
check_resource() {
    local resource_type=$1
    local resource_name=$2
    local description=$3
    
    case $resource_type in
        "lambda")
            if aws lambda get-function --function-name "$resource_name" --region "$REGION" >/dev/null 2>&1; then
                local state=$(aws lambda get-function --function-name "$resource_name" --region "$REGION" --query 'Configuration.State' --output text 2>/dev/null)
                local runtime=$(aws lambda get-function --function-name "$resource_name" --region "$REGION" --query 'Configuration.Runtime' --output text 2>/dev/null)
                local memory=$(aws lambda get-function --function-name "$resource_name" --region "$REGION" --query 'Configuration.MemorySize' --output text 2>/dev/null)
                local timeout=$(aws lambda get-function --function-name "$resource_name" --region "$REGION" --query 'Configuration.Timeout' --output text 2>/dev/null)
                echo -e "  ${GREEN}✓${NC} $description"
                echo -e "      State: ${state}, Runtime: ${runtime}, Memory: ${memory}MB, Timeout: ${timeout}s"
            else
                echo -e "  ${RED}✗${NC} $description"
            fi
            ;;
        "eventbridge")
            if aws events describe-rule --name "$resource_name" --region "$REGION" >/dev/null 2>&1; then
                local state=$(aws events describe-rule --name "$resource_name" --region "$REGION" --query 'State' --output text 2>/dev/null)
                local schedule=$(aws events describe-rule --name "$resource_name" --region "$REGION" --query 'ScheduleExpression' --output text 2>/dev/null)
                echo -e "  ${GREEN}✓${NC} $description"
                echo -e "      State: ${state}, Schedule: ${schedule}"
            else
                echo -e "  ${RED}✗${NC} $description"
            fi
            ;;
        "firehose")
            if aws firehose describe-delivery-stream --delivery-stream-name "$resource_name" --region "$REGION" >/dev/null 2>&1; then
                local status=$(aws firehose describe-delivery-stream --delivery-stream-name "$resource_name" --region "$REGION" --query 'DeliveryStreamDescription.DeliveryStreamStatus' --output text 2>/dev/null)
                local source=$(aws firehose describe-delivery-stream --delivery-stream-name "$resource_name" --region "$REGION" --query 'DeliveryStreamDescription.Source.MSKSourceDescription.TopicName' --output text 2>/dev/null)
                echo -e "  ${GREEN}✓${NC} $description"
                echo -e "      Status: ${status}, Source Topic: ${source}"
            else
                echo -e "  ${RED}✗${NC} $description"
            fi
            ;;
        "loggroup")
            if aws logs describe-log-groups --log-group-name-prefix "$resource_name" --region "$REGION" --query 'logGroups[0]' --output text >/dev/null 2>&1; then
                local size=$(aws logs describe-log-groups --log-group-name-prefix "$resource_name" --region "$REGION" --query 'logGroups[0].storedBytes' --output text 2>/dev/null)
                local size_mb=$(echo "scale=2; $size / 1048576" | bc 2>/dev/null || echo "0")
                echo -e "  ${GREEN}✓${NC} $description (${size_mb}MB)"
            else
                echo -e "  ${RED}✗${NC} $description"
            fi
            ;;
    esac
}

# 1. Lambda Functions
echo -e "${BLUE}═══ Lambda Functions ═══${NC}"
check_resource "lambda" "AcmeTelemetry-Generator" "Generator Function"
check_resource "lambda" "AcmeTelemetry-Producer" "Producer Function"
check_resource "lambda" "AcmeTelemetry-TopicManager" "Topic Manager Function"

# 2. EventBridge Rules
echo ""
echo -e "${BLUE}═══ EventBridge Rules ═══${NC}"
check_resource "eventbridge" "AcmeTelemetry-GeneratorSchedule" "Generator Schedule"

# 3. Kinesis Data Firehose
echo ""
echo -e "${BLUE}═══ Kinesis Data Firehose ═══${NC}"
check_resource "firehose" "AcmeTelemetry-MSK-to-S3" "MSK to S3 Delivery Stream"

# 4. CloudWatch Log Groups
echo ""
echo -e "${BLUE}═══ CloudWatch Log Groups ═══${NC}"
check_resource "loggroup" "/aws/lambda/AcmeTelemetry-Generator" "Generator Logs"
check_resource "loggroup" "/aws/lambda/AcmeTelemetry-Producer" "Producer Logs"
check_resource "loggroup" "/aws/kinesisfirehose/AcmeTelemetry-MSK-to-S3" "Firehose Logs"

# 5. MSK Cluster Info
echo ""
echo -e "${BLUE}═══ MSK Cluster ═══${NC}"
MSK_ARN="arn:aws:kafka:us-west-2:878687028155:cluster/simple-msk-us-west-2/05a8cbf7-ea44-42d5-a3ca-2d78cc557cc5-6"
if aws kafka describe-cluster --cluster-arn "$MSK_ARN" --region "$REGION" >/dev/null 2>&1; then
    CLUSTER_STATE=$(aws kafka describe-cluster --cluster-arn "$MSK_ARN" --region "$REGION" --query 'ClusterInfo.State' --output text 2>/dev/null)
    KAFKA_VERSION=$(aws kafka describe-cluster --cluster-arn "$MSK_ARN" --region "$REGION" --query 'ClusterInfo.CurrentBrokerSoftwareInfo.KafkaVersion' --output text 2>/dev/null)
    echo -e "  ${GREEN}✓${NC} MSK Cluster: simple-msk-us-west-2"
    echo -e "      State: ${CLUSTER_STATE}, Kafka Version: ${KAFKA_VERSION}"
else
    echo -e "  ${RED}✗${NC} MSK Cluster not accessible"
fi

# 6. S3 Data Statistics
echo ""
echo -e "${BLUE}═══ S3 Data Storage ═══${NC}"
echo -e "  Bucket: ${S3_BUCKET}"

# Count files and calculate size
FILE_COUNT=$(aws s3 ls "s3://${S3_BUCKET}/telemetry/" --recursive --region "$REGION" 2>/dev/null | wc -l || echo "0")
if [ "$FILE_COUNT" -gt 0 ]; then
    # Get total size
    TOTAL_SIZE=$(aws s3 ls "s3://${S3_BUCKET}/telemetry/" --recursive --summarize --region "$REGION" 2>/dev/null | grep "Total Size" | awk '{print $3}')
    TOTAL_SIZE_MB=$(echo "scale=2; ${TOTAL_SIZE:-0} / 1048576" | bc 2>/dev/null || echo "0")
    
    echo -e "  ${GREEN}✓${NC} Data Files: ${FILE_COUNT} files"
    echo -e "      Total Size: ${TOTAL_SIZE_MB}MB"
    
    # Show recent files
    echo -e "      Recent files:"
    aws s3 ls "s3://${S3_BUCKET}/telemetry/" --recursive --region "$REGION" 2>/dev/null | tail -3 | while read -r line; do
        echo -e "        $line"
    done
else
    echo -e "  ${YELLOW}⚠${NC} No data files found"
fi

# 7. Recent Lambda Invocations
echo ""
echo -e "${BLUE}═══ Recent Activity (Last 5 minutes) ═══${NC}"

# Check Generator invocations
GENERATOR_INVOCATIONS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=AcmeTelemetry-Generator \
    --start-time $(date -u -v-5M '+%Y-%m-%dT%H:%M:%S') \
    --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
    --period 300 \
    --statistics Sum \
    --region "$REGION" \
    --query 'Datapoints[0].Sum' \
    --output text 2>/dev/null || echo "0")

GENERATOR_ERRORS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Errors \
    --dimensions Name=FunctionName,Value=AcmeTelemetry-Generator \
    --start-time $(date -u -v-5M '+%Y-%m-%dT%H:%M:%S') \
    --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
    --period 300 \
    --statistics Sum \
    --region "$REGION" \
    --query 'Datapoints[0].Sum' \
    --output text 2>/dev/null || echo "0")

if [ "$GENERATOR_INVOCATIONS" != "0" ] && [ "$GENERATOR_INVOCATIONS" != "None" ]; then
    echo -e "  Generator: ${GENERATOR_INVOCATIONS} invocations, ${GENERATOR_ERRORS} errors"
else
    echo -e "  Generator: No recent activity"
fi

# Check Producer invocations
PRODUCER_INVOCATIONS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=AcmeTelemetry-Producer \
    --start-time $(date -u -v-5M '+%Y-%m-%dT%H:%M:%S') \
    --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
    --period 300 \
    --statistics Sum \
    --region "$REGION" \
    --query 'Datapoints[0].Sum' \
    --output text 2>/dev/null || echo "0")

if [ "$PRODUCER_INVOCATIONS" != "0" ] && [ "$PRODUCER_INVOCATIONS" != "None" ]; then
    echo -e "  Producer: ${PRODUCER_INVOCATIONS} invocations"
else
    echo -e "  Producer: No recent activity"
fi

# 8. Cost Estimation
echo ""
echo -e "${BLUE}═══ Monthly Cost Estimate ═══${NC}"
echo -e "  ${YELLOW}Note: These are rough estimates${NC}"
echo "  Lambda Invocations: ~\$10-20/month"
echo "  Lambda Duration: ~\$5-10/month"
echo "  Firehose: ~\$20-40/month"
echo "  S3 Storage: ~\$5-10/month"
echo "  CloudWatch Logs: ~\$5-10/month"
echo -e "  ${YELLOW}Estimated Total: \$45-90/month${NC}"

# 9. Summary
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}Pipeline Status Summary${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"

# Count deployed resources
LAMBDA_COUNT=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'AcmeTelemetry')].FunctionName" --output json --region "$REGION" 2>/dev/null | jq length || echo "0")
RULE_COUNT=$(aws events list-rules --name-prefix "AcmeTelemetry" --region "$REGION" --query 'Rules' --output json 2>/dev/null | jq length || echo "0")
FIREHOSE_COUNT=$(aws firehose list-delivery-streams --region "$REGION" --query "DeliveryStreamNames[?contains(@, 'AcmeTelemetry')]" --output json 2>/dev/null | jq length || echo "0")

echo "  Lambda Functions: ${LAMBDA_COUNT} deployed"
echo "  EventBridge Rules: ${RULE_COUNT} active"
echo "  Firehose Streams: ${FIREHOSE_COUNT} running"
echo "  S3 Data Files: ${FILE_COUNT} stored"

if [ "$LAMBDA_COUNT" -gt 0 ] && [ "$RULE_COUNT" -gt 0 ] && [ "$FIREHOSE_COUNT" -gt 0 ]; then
    echo ""
    echo -e "  ${GREEN}✅ Pipeline appears to be fully deployed${NC}"
else
    echo ""
    echo -e "  ${YELLOW}⚠️  Some components may be missing${NC}"
fi

echo ""
echo "To cleanup all resources, run: ./cleanup_pipeline.sh"