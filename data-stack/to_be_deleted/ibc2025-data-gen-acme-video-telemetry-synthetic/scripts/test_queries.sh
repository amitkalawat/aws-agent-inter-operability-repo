#!/bin/bash

# Test Queries for ACME Telemetry Analytics
# Usage: ./test_queries.sh

set -e

echo "🔍 Running ACME Telemetry Test Queries..."

# Configuration
REGION="eu-central-1"
DATABASE="acme_telemetry"
OUTPUT_LOCATION="s3://acme-telemetry-241533163649-eu-central-1/athena-results/"
DATE=$(date +%Y-%m-%d)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run query and get results
run_query() {
    local query="$1"
    local description="$2"
    
    echo -e "${YELLOW}Running: ${description}${NC}"
    
    # Start query execution
    QUERY_ID=$(aws athena start-query-execution \
        --query-string "$query" \
        --query-execution-context "Database=${DATABASE}" \
        --result-configuration "OutputLocation=${OUTPUT_LOCATION}" \
        --region $REGION \
        --output text)
    
    # Wait for query to complete
    echo -n "Waiting for query to complete..."
    while true; do
        STATUS=$(aws athena get-query-execution \
            --query-execution-id $QUERY_ID \
            --region $REGION \
            --query 'QueryExecution.Status.State' \
            --output text)
        
        if [ "$STATUS" = "SUCCEEDED" ]; then
            echo -e " ${GREEN}Done${NC}"
            break
        elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "CANCELLED" ]; then
            echo -e " ${RED}Failed${NC}"
            aws athena get-query-execution \
                --query-execution-id $QUERY_ID \
                --region $REGION \
                --query 'QueryExecution.Status.StateChangeReason' \
                --output text
            return 1
        fi
        sleep 1
        echo -n "."
    done
    
    # Get results
    aws athena get-query-results \
        --query-execution-id $QUERY_ID \
        --region $REGION \
        --output table \
        --max-items 20
    
    echo ""
}

# 0. First repair partitions
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Repairing table partitions...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
run_query "MSCK REPAIR TABLE video_telemetry_json" "Repair Partitions"

# 1. Basic Statistics
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}1. BASIC STATISTICS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY1="
SELECT 
    COUNT(*) as total_events,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT title_id) as unique_titles,
    COUNT(DISTINCT session_id) as unique_sessions
FROM video_telemetry_json
WHERE year = YEAR(CURRENT_DATE) 
  AND month = MONTH(CURRENT_DATE) 
  AND day = DAY(CURRENT_DATE)
"
run_query "$QUERY1" "Overall Statistics for Today"

# 2. Event Type Distribution
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}2. EVENT TYPE DISTRIBUTION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY2="
SELECT 
    event_type,
    COUNT(*) as event_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM video_telemetry_json
WHERE year = YEAR(CURRENT_DATE) 
  AND month = MONTH(CURRENT_DATE) 
  AND day = DAY(CURRENT_DATE)
GROUP BY event_type
ORDER BY event_count DESC
"
run_query "$QUERY2" "Event Type Distribution"

# 3. Top Titles with Metadata
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}3. TOP TITLES WITH METADATA${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY3="
SELECT 
    vt.title_id,
    t.title_name,
    t.genre,
    t.release_year,
    COUNT(*) as view_count,
    COUNT(DISTINCT vt.customer_id) as unique_viewers,
    ROUND(AVG(vt.completion_percentage), 2) as avg_completion
FROM video_telemetry_json vt
JOIN acme_streaming_data.titles t ON vt.title_id = t.title_id
WHERE vt.year = YEAR(CURRENT_DATE) 
  AND vt.month = MONTH(CURRENT_DATE) 
  AND vt.day = DAY(CURRENT_DATE)
GROUP BY vt.title_id, t.title_name, t.genre, t.release_year
ORDER BY view_count DESC
LIMIT 10
"
run_query "$QUERY3" "Top 10 Titles with Details"

# 4. Customer Segment Analysis
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}4. CUSTOMER SEGMENT ANALYSIS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY4="
SELECT 
    c.subscription_tier,
    c.age_group,
    COUNT(DISTINCT vt.customer_id) as active_customers,
    COUNT(*) as total_events,
    ROUND(AVG(vt.watch_duration_seconds), 0) as avg_watch_duration,
    ROUND(AVG(vt.completion_percentage), 2) as avg_completion
FROM video_telemetry_json vt
JOIN acme_streaming_data.customers c ON vt.customer_id = c.customer_id
WHERE vt.year = YEAR(CURRENT_DATE) 
  AND vt.month = MONTH(CURRENT_DATE) 
  AND vt.day = DAY(CURRENT_DATE)
GROUP BY c.subscription_tier, c.age_group
ORDER BY active_customers DESC
LIMIT 10
"
run_query "$QUERY4" "Customer Segment Behavior"

# 5. Streaming Quality Metrics
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}5. STREAMING QUALITY METRICS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY5="
SELECT 
    quality,
    device_type,
    COUNT(*) as stream_count,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth,
    ROUND(AVG(buffering_events), 2) as avg_buffering,
    SUM(error_count) as total_errors
FROM video_telemetry_json
WHERE year = YEAR(CURRENT_DATE) 
  AND month = MONTH(CURRENT_DATE) 
  AND vt.day = DAY(CURRENT_DATE)
GROUP BY quality, device_type
ORDER BY stream_count DESC
LIMIT 10
"
run_query "$QUERY5" "Quality and Device Performance"

# 6. Geographic Distribution
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}6. GEOGRAPHIC DISTRIBUTION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY6="
SELECT 
    country,
    state,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(*) as total_events,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth
FROM video_telemetry_json
WHERE year = YEAR(CURRENT_DATE) 
  AND month = MONTH(CURRENT_DATE) 
  AND day = DAY(CURRENT_DATE)
  AND state != ''
GROUP BY country, state
ORDER BY total_events DESC
LIMIT 10
"
run_query "$QUERY6" "Top Locations by Activity"

# 7. Content Performance by Genre
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}7. CONTENT PERFORMANCE BY GENRE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY7="
SELECT 
    t.genre,
    COUNT(DISTINCT vt.title_id) as unique_titles,
    COUNT(DISTINCT vt.customer_id) as unique_viewers,
    COUNT(*) as total_events,
    ROUND(AVG(vt.completion_percentage), 2) as avg_completion,
    SUM(CASE WHEN vt.event_type = 'complete' THEN 1 ELSE 0 END) as completions
FROM video_telemetry_json vt
JOIN acme_streaming_data.titles t ON vt.title_id = t.title_id
WHERE vt.year = YEAR(CURRENT_DATE) 
  AND vt.month = MONTH(CURRENT_DATE) 
  AND vt.day = DAY(CURRENT_DATE)
GROUP BY t.genre
ORDER BY total_events DESC
"
run_query "$QUERY7" "Genre Performance Metrics"

# 8. ISP Performance
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}8. ISP PERFORMANCE ANALYSIS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY8="
SELECT 
    isp,
    connection_type,
    COUNT(*) as stream_count,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth,
    ROUND(AVG(buffering_events), 2) as avg_buffering,
    SUM(error_count) as total_errors
FROM video_telemetry_json
WHERE year = YEAR(CURRENT_DATE) 
  AND month = MONTH(CURRENT_DATE) 
  AND day = DAY(CURRENT_DATE)
GROUP BY isp, connection_type
HAVING COUNT(*) > 10
ORDER BY avg_bandwidth DESC
LIMIT 10
"
run_query "$QUERY8" "ISP and Connection Performance"

# 9. Hourly Viewing Pattern
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}9. HOURLY VIEWING PATTERN${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY9="
SELECT 
    hour,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(*) as total_events,
    SUM(CASE WHEN event_type = 'start' THEN 1 ELSE 0 END) as new_sessions,
    SUM(CASE WHEN event_type = 'complete' THEN 1 ELSE 0 END) as completed_views
FROM video_telemetry_json
WHERE year = YEAR(CURRENT_DATE) 
  AND month = MONTH(CURRENT_DATE) 
  AND day = DAY(CURRENT_DATE)
GROUP BY hour
ORDER BY hour
"
run_query "$QUERY9" "Hourly Activity Pattern"

# 10. Data Quality Check
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}10. DATA QUALITY CHECK${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

QUERY10="
SELECT 
    'Real Title IDs' as check_type,
    COUNT(DISTINCT vt.title_id) as matched_count,
    COUNT(DISTINCT CASE WHEN t.title_id IS NULL THEN vt.title_id END) as unmatched_count
FROM video_telemetry_json vt
LEFT JOIN acme_streaming_data.titles t ON vt.title_id = t.title_id
WHERE vt.year = YEAR(CURRENT_DATE) 
  AND vt.month = MONTH(CURRENT_DATE) 
  AND vt.day = DAY(CURRENT_DATE)
UNION ALL
SELECT 
    'Real Customer IDs' as check_type,
    COUNT(DISTINCT vt.customer_id) as matched_count,
    COUNT(DISTINCT CASE WHEN c.customer_id IS NULL THEN vt.customer_id END) as unmatched_count
FROM video_telemetry_json vt
LEFT JOIN acme_streaming_data.customers c ON vt.customer_id = c.customer_id
WHERE vt.year = YEAR(CURRENT_DATE) 
  AND vt.month = MONTH(CURRENT_DATE) 
  AND vt.day = DAY(CURRENT_DATE)
"
run_query "$QUERY10" "Data Correlation Validation"

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All test queries completed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"