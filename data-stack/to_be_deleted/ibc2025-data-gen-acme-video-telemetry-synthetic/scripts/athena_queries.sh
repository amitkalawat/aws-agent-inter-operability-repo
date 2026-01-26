#!/bin/bash

# ACME Telemetry - Athena Analytics Queries
# Run various analytical queries on telemetry data

set -e

echo "📊 ACME Telemetry - Athena Analytics"
echo "====================================="
echo ""

# Configuration
DATABASE="acme_telemetry"
TABLE="video_telemetry_json"
REGION="us-west-2"
OUTPUT_LOCATION="s3://acme-telemetry-878687028155-us-west-2/athena-results/"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to run query and get results
run_query() {
    local query="$1"
    local description="$2"
    
    echo -e "${BLUE}Running: ${description}${NC}"
    
    # Start query execution
    query_id=$(aws athena start-query-execution \
        --query-string "$query" \
        --query-execution-context "Database=$DATABASE" \
        --result-configuration "OutputLocation=$OUTPUT_LOCATION" \
        --region "$REGION" \
        --output json | jq -r '.QueryExecutionId')
    
    # Wait for query to complete
    echo -n "Executing"
    for i in {1..10}; do
        sleep 1
        echo -n "."
        status=$(aws athena get-query-execution \
            --query-execution-id "$query_id" \
            --region "$REGION" \
            --query 'QueryExecution.Status.State' \
            --output text)
        
        if [ "$status" == "SUCCEEDED" ]; then
            echo " Done!"
            break
        elif [ "$status" == "FAILED" ]; then
            echo " Failed!"
            return 1
        fi
    done
    
    # Get results
    aws athena get-query-results \
        --query-execution-id "$query_id" \
        --region "$REGION" \
        --output table
    
    echo ""
}

# 1. Overview Statistics
echo -e "${YELLOW}═══ 1. OVERVIEW STATISTICS ═══${NC}"
run_query "
SELECT 
    COUNT(*) as total_events,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT title_id) as unique_titles,
    MIN(event_timestamp) as earliest_event,
    MAX(event_timestamp) as latest_event
FROM $TABLE
" "Overview Statistics"

# 2. Event Type Distribution
echo -e "${YELLOW}═══ 2. EVENT TYPE DISTRIBUTION ═══${NC}"
run_query "
SELECT 
    event_type,
    COUNT(*) as event_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM $TABLE
GROUP BY event_type
ORDER BY event_count DESC
" "Event Type Distribution"

# 3. Device Type Analysis
echo -e "${YELLOW}═══ 3. DEVICE TYPE ANALYSIS ═══${NC}"
run_query "
SELECT 
    device_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT customer_id) as unique_users,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth,
    ROUND(AVG(completion_percentage), 2) as avg_completion
FROM $TABLE
GROUP BY device_type
ORDER BY event_count DESC
" "Device Type Analysis"

# 4. Video Quality Distribution
echo -e "${YELLOW}═══ 4. VIDEO QUALITY DISTRIBUTION ═══${NC}"
run_query "
SELECT 
    quality,
    COUNT(*) as stream_count,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth,
    ROUND(AVG(buffering_events), 2) as avg_buffering,
    ROUND(AVG(completion_percentage), 2) as avg_completion
FROM $TABLE
GROUP BY quality
ORDER BY stream_count DESC
" "Video Quality Analysis"

# 5. Geographic Distribution
echo -e "${YELLOW}═══ 5. GEOGRAPHIC DISTRIBUTION ═══${NC}"
run_query "
SELECT 
    country,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(*) as total_events,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth
FROM $TABLE
GROUP BY country
ORDER BY unique_viewers DESC
LIMIT 10
" "Geographic Distribution"

# 6. ISP Performance
echo -e "${YELLOW}═══ 6. ISP PERFORMANCE ═══${NC}"
run_query "
SELECT 
    isp,
    COUNT(*) as events,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth,
    ROUND(AVG(buffering_events), 2) as avg_buffering,
    SUM(error_count) as total_errors
FROM $TABLE
GROUP BY isp
HAVING COUNT(*) > 5
ORDER BY avg_bandwidth DESC
" "ISP Performance Analysis"

# 7. Viewing Behavior by Hour
echo -e "${YELLOW}═══ 7. VIEWING PATTERNS BY HOUR ═══${NC}"
run_query "
SELECT 
    hour,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(*) as total_events,
    ROUND(AVG(watch_duration_seconds/60.0), 2) as avg_watch_minutes
FROM $TABLE
GROUP BY hour
ORDER BY hour
" "Hourly Viewing Patterns"

# 8. Top Content
echo -e "${YELLOW}═══ 8. TOP CONTENT ═══${NC}"
run_query "
SELECT 
    title_id,
    COUNT(DISTINCT customer_id) as unique_viewers,
    COUNT(*) as total_plays,
    ROUND(AVG(completion_percentage), 2) as avg_completion,
    ROUND(AVG(watch_duration_seconds/60.0), 2) as avg_watch_minutes
FROM $TABLE
WHERE event_type IN ('start', 'complete')
GROUP BY title_id
ORDER BY unique_viewers DESC
LIMIT 10
" "Top Content by Viewers"

# 9. Buffering Analysis
echo -e "${YELLOW}═══ 9. BUFFERING ANALYSIS ═══${NC}"
run_query "
SELECT 
    CASE 
        WHEN buffering_events = 0 THEN 'No Buffering'
        WHEN buffering_events BETWEEN 1 AND 2 THEN 'Light (1-2)'
        WHEN buffering_events BETWEEN 3 AND 5 THEN 'Moderate (3-5)'
        ELSE 'Heavy (>5)'
    END as buffering_category,
    COUNT(*) as session_count,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth,
    ROUND(AVG(completion_percentage), 2) as avg_completion
FROM $TABLE
GROUP BY 
    CASE 
        WHEN buffering_events = 0 THEN 'No Buffering'
        WHEN buffering_events BETWEEN 1 AND 2 THEN 'Light (1-2)'
        WHEN buffering_events BETWEEN 3 AND 5 THEN 'Moderate (3-5)'
        ELSE 'Heavy (>5)'
    END
ORDER BY session_count DESC
" "Buffering Impact Analysis"

# 10. Connection Type Performance
echo -e "${YELLOW}═══ 10. CONNECTION TYPE PERFORMANCE ═══${NC}"
run_query "
SELECT 
    connection_type,
    COUNT(*) as events,
    ROUND(AVG(bandwidth_mbps), 2) as avg_bandwidth,
    ROUND(AVG(buffering_events), 2) as avg_buffering,
    ROUND(AVG(completion_percentage), 2) as avg_completion
FROM $TABLE
GROUP BY connection_type
ORDER BY avg_bandwidth DESC
" "Connection Type Performance"

# 11. Error Analysis
echo -e "${YELLOW}═══ 11. ERROR ANALYSIS ═══${NC}"
run_query "
SELECT 
    CASE 
        WHEN error_count = 0 THEN 'No Errors'
        WHEN error_count = 1 THEN '1 Error'
        WHEN error_count = 2 THEN '2 Errors'
        ELSE '3+ Errors'
    END as error_category,
    COUNT(*) as session_count,
    ROUND(AVG(completion_percentage), 2) as avg_completion,
    device_type
FROM $TABLE
GROUP BY 
    CASE 
        WHEN error_count = 0 THEN 'No Errors'
        WHEN error_count = 1 THEN '1 Error'
        WHEN error_count = 2 THEN '2 Errors'
        ELSE '3+ Errors'
    END,
    device_type
ORDER BY session_count DESC
" "Error Impact by Device"

# 12. Completion Rate Analysis
echo -e "${YELLOW}═══ 12. COMPLETION RATE ANALYSIS ═══${NC}"
run_query "
SELECT 
    CASE 
        WHEN completion_percentage >= 90 THEN 'Completed (90%+)'
        WHEN completion_percentage >= 75 THEN 'Mostly Watched (75-90%)'
        WHEN completion_percentage >= 50 THEN 'Half Watched (50-75%)'
        WHEN completion_percentage >= 25 THEN 'Partially Watched (25-50%)'
        ELSE 'Early Exit (<25%)'
    END as completion_category,
    COUNT(*) as session_count,
    ROUND(AVG(watch_duration_seconds/60.0), 2) as avg_watch_minutes
FROM $TABLE
WHERE event_type IN ('stop', 'complete')
GROUP BY 
    CASE 
        WHEN completion_percentage >= 90 THEN 'Completed (90%+)'
        WHEN completion_percentage >= 75 THEN 'Mostly Watched (75-90%)'
        WHEN completion_percentage >= 50 THEN 'Half Watched (50-75%)'
        WHEN completion_percentage >= 25 THEN 'Partially Watched (25-50%)'
        ELSE 'Early Exit (<25%)'
    END
ORDER BY session_count DESC
" "Completion Rate Distribution"

echo ""
echo -e "${GREEN}═══ ANALYSIS COMPLETE ═══${NC}"
echo ""
echo "Results saved to: $OUTPUT_LOCATION"
echo "To run custom queries, use:"
echo "  aws athena start-query-execution --query-string 'YOUR_QUERY' --query-execution-context 'Database=$DATABASE'"