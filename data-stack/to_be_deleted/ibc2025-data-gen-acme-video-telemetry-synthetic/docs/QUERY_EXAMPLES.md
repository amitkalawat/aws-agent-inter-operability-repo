# ACME Telemetry - Query Examples Library

## Overview

This document provides a comprehensive library of Athena SQL queries for analyzing ACME video streaming telemetry data. Queries are organized by business use case and analytics objective.

## 📊 Business Intelligence Queries

### Executive Dashboard Queries

#### Daily Active Users (DAU) and Monthly Active Users (MAU)
```sql
-- Daily Active Users with trend
WITH daily_users AS (
    SELECT 
        DATE(event_timestamp) as event_date,
        COUNT(DISTINCT customer_id) as dau,
        COUNT(DISTINCT session_id) as daily_sessions,
        SUM(watch_duration_seconds) / 3600.0 as total_hours_watched
    FROM acme_telemetry.video_telemetry_json
    WHERE year = YEAR(CURRENT_DATE) 
      AND month = MONTH(CURRENT_DATE)
    GROUP BY DATE(event_timestamp)
)
SELECT 
    event_date,
    dau,
    daily_sessions,
    ROUND(total_hours_watched, 2) as total_hours,
    ROUND(total_hours_watched / dau, 2) as hours_per_user,
    ROUND(100.0 * (dau - LAG(dau, 1) OVER (ORDER BY event_date)) / LAG(dau, 1) OVER (ORDER BY event_date), 2) as dau_growth_pct
FROM daily_users
ORDER BY event_date DESC;

-- Monthly Active Users
SELECT 
    year,
    month,
    COUNT(DISTINCT customer_id) as mau,
    COUNT(DISTINCT session_id) as monthly_sessions,
    ROUND(SUM(watch_duration_seconds) / 3600.0, 2) as total_hours_watched,
    COUNT(DISTINCT title_id) as unique_titles_watched
FROM acme_telemetry.video_telemetry_json
GROUP BY year, month
ORDER BY year DESC, month DESC;
```

#### Revenue Impact Metrics
```sql
-- Viewer segments by engagement (for revenue modeling)
WITH user_engagement AS (
    SELECT 
        customer_id,
        COUNT(DISTINCT DATE(event_timestamp)) as active_days,
        COUNT(DISTINCT session_id) as total_sessions,
        SUM(watch_duration_seconds) / 3600.0 as total_hours,
        AVG(completion_percentage) as avg_completion,
        COUNT(DISTINCT title_id) as titles_watched
    FROM acme_telemetry.video_telemetry_json
    WHERE year = YEAR(CURRENT_DATE) 
      AND month = MONTH(CURRENT_DATE)
    GROUP BY customer_id
)
SELECT 
    CASE 
        WHEN total_hours >= 20 AND active_days >= 15 THEN 'Power Users'
        WHEN total_hours >= 10 AND active_days >= 7 THEN 'Regular Users'
        WHEN total_hours >= 5 THEN 'Casual Users'
        ELSE 'Light Users'
    END as user_segment,
    COUNT(*) as user_count,
    ROUND(AVG(total_hours), 2) as avg_hours,
    ROUND(AVG(active_days), 1) as avg_active_days,
    ROUND(AVG(titles_watched), 1) as avg_titles
FROM user_engagement
GROUP BY 
    CASE 
        WHEN total_hours >= 20 AND active_days >= 15 THEN 'Power Users'
        WHEN total_hours >= 10 AND active_days >= 7 THEN 'Regular Users'
        WHEN total_hours >= 5 THEN 'Casual Users'
        ELSE 'Light Users'
    END
ORDER BY user_count DESC;
```

### Content Performance Analytics

#### Top Performing Content
```sql
-- Content performance scorecard
WITH content_metrics AS (
    SELECT 
        title_id,
        COUNT(DISTINCT customer_id) as unique_viewers,
        COUNT(CASE WHEN event_type = 'start' THEN 1 END) as starts,
        COUNT(CASE WHEN event_type = 'complete' THEN 1 END) as completions,
        AVG(CASE WHEN event_type IN ('stop', 'complete') THEN completion_percentage END) as avg_completion,
        SUM(watch_duration_seconds) / 3600.0 as total_hours_watched,
        AVG(CASE WHEN event_type = 'start' THEN bandwidth_mbps END) as avg_start_bandwidth
    FROM acme_telemetry.video_telemetry_json
    GROUP BY title_id
)
SELECT 
    title_id,
    unique_viewers,
    starts,
    completions,
    ROUND(100.0 * completions / NULLIF(starts, 0), 2) as completion_rate,
    ROUND(avg_completion, 2) as avg_completion_pct,
    ROUND(total_hours_watched, 2) as total_hours,
    ROUND(total_hours_watched / NULLIF(unique_viewers, 0), 2) as hours_per_viewer,
    -- Performance score (weighted metric)
    ROUND(
        (unique_viewers * 0.3) + 
        (completion_rate * 0.4) + 
        (avg_completion * 0.3)
    , 2) as performance_score
FROM content_metrics
WHERE starts > 0
ORDER BY performance_score DESC
LIMIT 20;
```

#### Content Engagement Funnel
```sql
-- View-through funnel by content
SELECT 
    title_id,
    COUNT(DISTINCT CASE WHEN event_type = 'start' THEN session_id END) as started,
    COUNT(DISTINCT CASE WHEN completion_percentage >= 25 THEN session_id END) as reached_25pct,
    COUNT(DISTINCT CASE WHEN completion_percentage >= 50 THEN session_id END) as reached_50pct,
    COUNT(DISTINCT CASE WHEN completion_percentage >= 75 THEN session_id END) as reached_75pct,
    COUNT(DISTINCT CASE WHEN event_type = 'complete' THEN session_id END) as completed,
    -- Conversion rates
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN completion_percentage >= 25 THEN session_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'start' THEN session_id END), 0), 2) as pct_25,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN completion_percentage >= 50 THEN session_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'start' THEN session_id END), 0), 2) as pct_50,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN completion_percentage >= 75 THEN session_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'start' THEN session_id END), 0), 2) as pct_75,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'complete' THEN session_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'start' THEN session_id END), 0), 2) as pct_complete
FROM acme_telemetry.video_telemetry_json
GROUP BY title_id
HAVING COUNT(DISTINCT CASE WHEN event_type = 'start' THEN session_id END) >= 10
ORDER BY started DESC;
```

## 🔧 Technical Performance Queries

### Quality of Service (QoS) Metrics

#### Buffering Analysis
```sql
-- Buffering impact on viewer experience
WITH session_buffering AS (
    SELECT 
        session_id,
        customer_id,
        MAX(buffering_events) as total_buffering_events,
        MAX(buffering_duration_seconds) as total_buffer_time,
        MAX(completion_percentage) as session_completion,
        MAX(watch_duration_seconds) as watch_duration,
        AVG(bandwidth_mbps) as avg_bandwidth,
        FIRST_VALUE(quality) OVER (PARTITION BY session_id ORDER BY event_timestamp) as stream_quality
    FROM acme_telemetry.video_telemetry_json
    GROUP BY session_id, customer_id
)
SELECT 
    CASE 
        WHEN total_buffering_events = 0 THEN '0 - Perfect'
        WHEN total_buffering_events <= 2 THEN '1-2 - Good'
        WHEN total_buffering_events <= 5 THEN '3-5 - Fair'
        ELSE '6+ - Poor'
    END as qos_category,
    COUNT(*) as session_count,
    ROUND(AVG(session_completion), 2) as avg_completion,
    ROUND(AVG(watch_duration) / 60.0, 2) as avg_watch_minutes,
    ROUND(AVG(total_buffer_time), 2) as avg_buffer_seconds,
    ROUND(AVG(avg_bandwidth), 2) as avg_bandwidth_mbps,
    -- Calculate abandonment rate
    ROUND(100.0 * COUNT(CASE WHEN session_completion < 10 THEN 1 END) / COUNT(*), 2) as early_abandon_rate
FROM session_buffering
GROUP BY 
    CASE 
        WHEN total_buffering_events = 0 THEN '0 - Perfect'
        WHEN total_buffering_events <= 2 THEN '1-2 - Good'
        WHEN total_buffering_events <= 5 THEN '3-5 - Fair'
        ELSE '6+ - Poor'
    END
ORDER BY session_count DESC;
```

#### Bandwidth Utilization
```sql
-- Bandwidth requirements by quality level
WITH bandwidth_stats AS (
    SELECT 
        quality,
        device_type,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY bandwidth_mbps) as p25_bandwidth,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY bandwidth_mbps) as p50_bandwidth,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY bandwidth_mbps) as p75_bandwidth,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY bandwidth_mbps) as p95_bandwidth,
        AVG(bandwidth_mbps) as avg_bandwidth,
        COUNT(*) as sample_count
    FROM acme_telemetry.video_telemetry_json
    WHERE bandwidth_mbps > 0
    GROUP BY quality, device_type
)
SELECT 
    quality,
    device_type,
    sample_count,
    ROUND(p25_bandwidth, 2) as p25_mbps,
    ROUND(p50_bandwidth, 2) as median_mbps,
    ROUND(p75_bandwidth, 2) as p75_mbps,
    ROUND(p95_bandwidth, 2) as p95_mbps,
    ROUND(avg_bandwidth, 2) as avg_mbps,
    -- Bandwidth sufficiency indicator
    CASE 
        WHEN quality = '4K' AND p50_bandwidth < 25 THEN 'Insufficient'
        WHEN quality = 'HD' AND p50_bandwidth < 5 THEN 'Insufficient'
        WHEN quality = 'SD' AND p50_bandwidth < 2.5 THEN 'Insufficient'
        ELSE 'Adequate'
    END as bandwidth_sufficiency
FROM bandwidth_stats
ORDER BY quality DESC, device_type;
```

### Error Analysis

#### Error Patterns and Impact
```sql
-- Error analysis by dimensions
WITH error_sessions AS (
    SELECT 
        session_id,
        customer_id,
        MAX(error_count) as session_errors,
        MAX(completion_percentage) as completion,
        MAX(watch_duration_seconds) as watch_duration,
        FIRST_VALUE(device_type) OVER (PARTITION BY session_id ORDER BY event_timestamp) as device,
        FIRST_VALUE(quality) OVER (PARTITION BY session_id ORDER BY event_timestamp) as quality,
        FIRST_VALUE(isp) OVER (PARTITION BY session_id ORDER BY event_timestamp) as isp,
        AVG(bandwidth_mbps) as avg_bandwidth
    FROM acme_telemetry.video_telemetry_json
    GROUP BY session_id, customer_id
)
SELECT 
    CASE 
        WHEN session_errors = 0 THEN 'No Errors'
        WHEN session_errors = 1 THEN '1 Error'
        WHEN session_errors <= 3 THEN '2-3 Errors'
        ELSE '4+ Errors'
    END as error_category,
    device,
    COUNT(*) as affected_sessions,
    ROUND(AVG(completion), 2) as avg_completion,
    ROUND(AVG(watch_duration) / 60.0, 2) as avg_watch_minutes,
    ROUND(AVG(avg_bandwidth), 2) as avg_bandwidth,
    -- Impact metrics
    COUNT(DISTINCT customer_id) as affected_users,
    ROUND(100.0 * COUNT(CASE WHEN completion < 10 THEN 1 END) / COUNT(*), 2) as abandonment_rate
FROM error_sessions
GROUP BY 
    CASE 
        WHEN session_errors = 0 THEN 'No Errors'
        WHEN session_errors = 1 THEN '1 Error'
        WHEN session_errors <= 3 THEN '2-3 Errors'
        ELSE '4+ Errors'
    END,
    device
HAVING COUNT(*) >= 5
ORDER BY error_category, affected_sessions DESC;
```

## 👥 User Behavior Analytics

### Viewing Patterns

#### Time-based Usage Patterns
```sql
-- Hourly viewing patterns with peak detection
WITH hourly_metrics AS (
    SELECT 
        hour,
        COUNT(DISTINCT customer_id) as unique_viewers,
        COUNT(DISTINCT session_id) as sessions,
        COUNT(CASE WHEN event_type = 'start' THEN 1 END) as new_starts,
        AVG(bandwidth_mbps) as avg_bandwidth,
        AVG(buffering_events) as avg_buffering
    FROM acme_telemetry.video_telemetry_json
    GROUP BY hour
),
peak_hours AS (
    SELECT 
        MAX(unique_viewers) as max_viewers,
        AVG(unique_viewers) as avg_viewers
    FROM hourly_metrics
)
SELECT 
    h.hour,
    h.unique_viewers,
    h.sessions,
    h.new_starts,
    ROUND(h.avg_bandwidth, 2) as avg_bandwidth_mbps,
    ROUND(h.avg_buffering, 2) as avg_buffering_events,
    CASE 
        WHEN h.unique_viewers >= p.max_viewers * 0.8 THEN 'Peak'
        WHEN h.unique_viewers >= p.avg_viewers THEN 'High'
        WHEN h.unique_viewers >= p.avg_viewers * 0.5 THEN 'Medium'
        ELSE 'Low'
    END as traffic_level,
    ROUND(100.0 * h.unique_viewers / SUM(h.unique_viewers) OVER (), 2) as pct_daily_traffic
FROM hourly_metrics h, peak_hours p
ORDER BY h.hour;
```

#### User Journey Analysis
```sql
-- Session progression patterns
WITH session_events AS (
    SELECT 
        session_id,
        customer_id,
        event_type,
        event_timestamp,
        completion_percentage,
        ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY event_timestamp) as event_sequence,
        LEAD(event_type) OVER (PARTITION BY session_id ORDER BY event_timestamp) as next_event
    FROM acme_telemetry.video_telemetry_json
)
SELECT 
    event_type as current_event,
    next_event,
    COUNT(*) as transition_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY event_type), 2) as transition_pct
FROM session_events
WHERE next_event IS NOT NULL
GROUP BY event_type, next_event
ORDER BY event_type, transition_count DESC;
```

### Device and Platform Analysis

#### Cross-Platform Performance
```sql
-- Device performance comparison
WITH device_metrics AS (
    SELECT 
        device_type,
        device_os,
        COUNT(DISTINCT customer_id) as users,
        COUNT(DISTINCT session_id) as sessions,
        AVG(completion_percentage) as avg_completion,
        AVG(bandwidth_mbps) as avg_bandwidth,
        AVG(buffering_events) as avg_buffering,
        SUM(error_count) as total_errors,
        -- Quality distribution
        COUNT(CASE WHEN quality = '4K' THEN 1 END) as quality_4k,
        COUNT(CASE WHEN quality = 'HD' THEN 1 END) as quality_hd,
        COUNT(CASE WHEN quality = 'SD' THEN 1 END) as quality_sd
    FROM acme_telemetry.video_telemetry_json
    GROUP BY device_type, device_os
)
SELECT 
    device_type,
    device_os,
    users,
    sessions,
    ROUND(avg_completion, 2) as avg_completion_pct,
    ROUND(avg_bandwidth, 2) as avg_bandwidth_mbps,
    ROUND(avg_buffering, 2) as avg_buffering_events,
    total_errors,
    -- Quality preference percentages
    ROUND(100.0 * quality_4k / sessions, 2) as pct_4k,
    ROUND(100.0 * quality_hd / sessions, 2) as pct_hd,
    ROUND(100.0 * quality_sd / sessions, 2) as pct_sd,
    -- Performance score
    ROUND(
        (avg_completion * 0.4) + 
        ((100 - avg_buffering * 10) * 0.3) + 
        ((100 - total_errors / sessions * 10) * 0.3)
    , 2) as performance_score
FROM device_metrics
ORDER BY users DESC;
```

## 🌍 Geographic Analytics

### Regional Performance

#### Geographic Distribution and Performance
```sql
-- Regional performance metrics
WITH regional_stats AS (
    SELECT 
        country,
        state,
        city,
        COUNT(DISTINCT customer_id) as unique_users,
        COUNT(DISTINCT session_id) as sessions,
        AVG(bandwidth_mbps) as avg_bandwidth,
        AVG(buffering_events) as avg_buffering,
        AVG(completion_percentage) as avg_completion,
        -- Network quality indicators
        COUNT(CASE WHEN connection_type = 'fiber' THEN 1 END) as fiber_sessions,
        COUNT(CASE WHEN connection_type = 'cable' THEN 1 END) as cable_sessions,
        COUNT(CASE WHEN connection_type = 'dsl' THEN 1 END) as dsl_sessions,
        COUNT(CASE WHEN connection_type = 'mobile' THEN 1 END) as mobile_sessions
    FROM acme_telemetry.video_telemetry_json
    GROUP BY country, state, city
)
SELECT 
    country,
    state,
    city,
    unique_users,
    sessions,
    ROUND(avg_bandwidth, 2) as avg_bandwidth_mbps,
    ROUND(avg_buffering, 2) as avg_buffering_events,
    ROUND(avg_completion, 2) as avg_completion_pct,
    -- Primary connection type
    CASE 
        WHEN fiber_sessions >= GREATEST(cable_sessions, dsl_sessions, mobile_sessions) THEN 'Fiber'
        WHEN cable_sessions >= GREATEST(fiber_sessions, dsl_sessions, mobile_sessions) THEN 'Cable'
        WHEN dsl_sessions >= GREATEST(fiber_sessions, cable_sessions, mobile_sessions) THEN 'DSL'
        ELSE 'Mobile'
    END as primary_connection,
    -- Performance rating
    CASE 
        WHEN avg_bandwidth >= 10 AND avg_buffering < 2 THEN 'Excellent'
        WHEN avg_bandwidth >= 5 AND avg_buffering < 3 THEN 'Good'
        WHEN avg_bandwidth >= 2.5 AND avg_buffering < 5 THEN 'Fair'
        ELSE 'Poor'
    END as performance_rating
FROM regional_stats
WHERE sessions >= 10
ORDER BY unique_users DESC;
```

### ISP Performance Comparison

#### ISP Quality Metrics
```sql
-- ISP performance scorecard
WITH isp_metrics AS (
    SELECT 
        isp,
        connection_type,
        COUNT(DISTINCT customer_id) as customers,
        COUNT(*) as events,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY bandwidth_mbps) as median_bandwidth,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY bandwidth_mbps) as p95_bandwidth,
        AVG(buffering_events) as avg_buffering,
        AVG(buffering_duration_seconds) as avg_buffer_duration,
        AVG(error_count) as avg_errors,
        AVG(completion_percentage) as avg_completion
    FROM acme_telemetry.video_telemetry_json
    GROUP BY isp, connection_type
    HAVING COUNT(*) >= 10
)
SELECT 
    isp,
    connection_type,
    customers,
    events,
    ROUND(median_bandwidth, 2) as median_mbps,
    ROUND(p95_bandwidth, 2) as p95_mbps,
    ROUND(avg_buffering, 2) as avg_buffering_events,
    ROUND(avg_buffer_duration, 2) as avg_buffer_seconds,
    ROUND(avg_errors, 2) as avg_error_count,
    ROUND(avg_completion, 2) as avg_completion_pct,
    -- ISP quality score (0-100)
    ROUND(
        GREATEST(0, LEAST(100,
            (median_bandwidth * 2) +  -- Weight bandwidth heavily
            (100 - avg_buffering * 10) * 0.3 +
            (100 - avg_errors * 20) * 0.2 +
            (avg_completion * 0.3)
        ))
    , 2) as quality_score
FROM isp_metrics
ORDER BY quality_score DESC;
```

## 📈 Trend Analysis

### Growth Metrics

#### User Growth Analysis
```sql
-- Daily new vs returning users
WITH user_first_seen AS (
    SELECT 
        customer_id,
        MIN(DATE(event_timestamp)) as first_seen_date
    FROM acme_telemetry.video_telemetry_json
    GROUP BY customer_id
),
daily_users AS (
    SELECT 
        DATE(t.event_timestamp) as event_date,
        t.customer_id,
        CASE 
            WHEN DATE(t.event_timestamp) = u.first_seen_date THEN 'New'
            ELSE 'Returning'
        END as user_type
    FROM acme_telemetry.video_telemetry_json t
    JOIN user_first_seen u ON t.customer_id = u.customer_id
)
SELECT 
    event_date,
    COUNT(DISTINCT CASE WHEN user_type = 'New' THEN customer_id END) as new_users,
    COUNT(DISTINCT CASE WHEN user_type = 'Returning' THEN customer_id END) as returning_users,
    COUNT(DISTINCT customer_id) as total_users,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN user_type = 'New' THEN customer_id END) / 
          COUNT(DISTINCT customer_id), 2) as new_user_pct,
    -- Cumulative users
    SUM(COUNT(DISTINCT CASE WHEN user_type = 'New' THEN customer_id END)) 
        OVER (ORDER BY event_date) as cumulative_users
FROM daily_users
GROUP BY event_date
ORDER BY event_date DESC;
```

### Retention Analysis

#### User Retention Cohorts
```sql
-- Weekly retention cohorts
WITH user_cohorts AS (
    SELECT 
        customer_id,
        DATE_TRUNC('week', MIN(event_timestamp)) as cohort_week,
        DATE_TRUNC('week', event_timestamp) as activity_week
    FROM acme_telemetry.video_telemetry_json
    GROUP BY customer_id, DATE_TRUNC('week', event_timestamp)
),
cohort_retention AS (
    SELECT 
        cohort_week,
        DATEDIFF('week', cohort_week, activity_week) as weeks_since_start,
        COUNT(DISTINCT customer_id) as retained_users
    FROM user_cohorts
    GROUP BY cohort_week, DATEDIFF('week', cohort_week, activity_week)
),
cohort_sizes AS (
    SELECT 
        cohort_week,
        COUNT(DISTINCT customer_id) as cohort_size
    FROM user_cohorts
    WHERE cohort_week = activity_week
    GROUP BY cohort_week
)
SELECT 
    c.cohort_week,
    r.weeks_since_start,
    r.retained_users,
    s.cohort_size,
    ROUND(100.0 * r.retained_users / s.cohort_size, 2) as retention_pct
FROM cohort_retention r
JOIN cohort_sizes s ON r.cohort_week = s.cohort_week
WHERE r.weeks_since_start <= 4
ORDER BY c.cohort_week DESC, r.weeks_since_start;
```

## 🎯 Advanced Analytics

### Predictive Indicators

#### Churn Risk Scoring
```sql
-- Identify users at risk of churning
WITH user_activity AS (
    SELECT 
        customer_id,
        COUNT(DISTINCT DATE(event_timestamp)) as active_days,
        MAX(DATE(event_timestamp)) as last_active_date,
        DATEDIFF('day', MAX(DATE(event_timestamp)), CURRENT_DATE) as days_since_active,
        COUNT(DISTINCT session_id) as total_sessions,
        AVG(completion_percentage) as avg_completion,
        AVG(buffering_events) as avg_buffering,
        SUM(error_count) as total_errors,
        SUM(watch_duration_seconds) / 3600.0 as total_hours_watched
    FROM acme_telemetry.video_telemetry_json
    WHERE year = YEAR(CURRENT_DATE) 
      AND month >= MONTH(CURRENT_DATE) - 1
    GROUP BY customer_id
)
SELECT 
    customer_id,
    active_days,
    days_since_active,
    total_sessions,
    ROUND(avg_completion, 2) as avg_completion_pct,
    ROUND(total_hours_watched, 2) as total_hours,
    -- Churn risk score (higher = more likely to churn)
    ROUND(
        (days_since_active * 2) +  -- Weight recency heavily
        (30 - active_days) +
        (100 - avg_completion) * 0.5 +
        (avg_buffering * 5) +
        (total_errors * 2) +
        (20 - total_sessions)
    , 2) as churn_risk_score,
    -- Risk category
    CASE 
        WHEN days_since_active > 14 THEN 'High Risk - Inactive'
        WHEN days_since_active > 7 AND avg_completion < 50 THEN 'High Risk - Disengaged'
        WHEN days_since_active > 7 THEN 'Medium Risk'
        WHEN avg_completion < 30 THEN 'Medium Risk - Low Engagement'
        ELSE 'Low Risk'
    END as risk_category
FROM user_activity
ORDER BY churn_risk_score DESC
LIMIT 100;
```

### A/B Testing Support

#### Quality Setting Impact Analysis
```sql
-- Compare user experience across quality settings
WITH quality_cohorts AS (
    SELECT 
        quality as test_group,
        COUNT(DISTINCT customer_id) as users,
        COUNT(DISTINCT session_id) as sessions,
        AVG(completion_percentage) as avg_completion,
        AVG(watch_duration_seconds) / 60.0 as avg_watch_minutes,
        AVG(buffering_events) as avg_buffering,
        AVG(buffering_duration_seconds) as avg_buffer_duration,
        SUM(error_count) as total_errors
    FROM acme_telemetry.video_telemetry_json
    GROUP BY quality
),
baseline AS (
    SELECT 
        AVG(completion_percentage) as baseline_completion,
        AVG(watch_duration_seconds) / 60.0 as baseline_watch_minutes
    FROM acme_telemetry.video_telemetry_json
    WHERE quality = 'HD'  -- HD as baseline
)
SELECT 
    q.test_group,
    q.users,
    q.sessions,
    ROUND(q.avg_completion, 2) as avg_completion_pct,
    ROUND(q.avg_watch_minutes, 2) as avg_watch_min,
    ROUND(q.avg_buffering, 2) as avg_buffer_events,
    ROUND(q.avg_buffer_duration, 2) as avg_buffer_sec,
    q.total_errors,
    -- Lift vs baseline
    ROUND(((q.avg_completion - b.baseline_completion) / b.baseline_completion) * 100, 2) as completion_lift_pct,
    ROUND(((q.avg_watch_minutes - b.baseline_watch_minutes) / b.baseline_watch_minutes) * 100, 2) as watch_time_lift_pct,
    -- Statistical significance indicator (simplified)
    CASE 
        WHEN q.sessions >= 100 AND ABS(q.avg_completion - b.baseline_completion) > 5 THEN 'Significant'
        WHEN q.sessions >= 50 THEN 'Marginal'
        ELSE 'Insufficient Data'
    END as significance
FROM quality_cohorts q, baseline b
ORDER BY q.avg_completion DESC;
```

## 🔍 Diagnostic Queries

### Data Quality Checks

#### Data Completeness Validation
```sql
-- Check for data quality issues
SELECT 
    'Total Records' as metric,
    COUNT(*) as value
FROM acme_telemetry.video_telemetry_json
UNION ALL
SELECT 
    'Null Event IDs' as metric,
    COUNT(*) as value
FROM acme_telemetry.video_telemetry_json
WHERE event_id IS NULL
UNION ALL
SELECT 
    'Null Customer IDs' as metric,
    COUNT(*) as value
FROM acme_telemetry.video_telemetry_json
WHERE customer_id IS NULL
UNION ALL
SELECT 
    'Invalid Timestamps' as metric,
    COUNT(*) as value
FROM acme_telemetry.video_telemetry_json
WHERE event_timestamp IS NULL OR event_timestamp = ''
UNION ALL
SELECT 
    'Negative Durations' as metric,
    COUNT(*) as value
FROM acme_telemetry.video_telemetry_json
WHERE watch_duration_seconds < 0
UNION ALL
SELECT 
    'Invalid Completion %' as metric,
    COUNT(*) as value
FROM acme_telemetry.video_telemetry_json
WHERE completion_percentage < 0 OR completion_percentage > 100
UNION ALL
SELECT 
    'Suspicious Bandwidth' as metric,
    COUNT(*) as value
FROM acme_telemetry.video_telemetry_json
WHERE bandwidth_mbps <= 0 OR bandwidth_mbps > 1000;
```

### System Health Monitoring

#### Real-time Pipeline Health
```sql
-- Monitor data freshness and pipeline health
WITH recent_data AS (
    SELECT 
        MAX(event_timestamp) as latest_event,
        MIN(event_timestamp) as earliest_event,
        COUNT(*) as total_events,
        COUNT(DISTINCT customer_id) as unique_users,
        COUNT(DISTINCT session_id) as unique_sessions
    FROM acme_telemetry.video_telemetry_json
    WHERE year = YEAR(CURRENT_DATE) 
      AND month = MONTH(CURRENT_DATE)
      AND day = DAY(CURRENT_DATE)
),
hourly_rate AS (
    SELECT 
        hour,
        COUNT(*) as events_per_hour
    FROM acme_telemetry.video_telemetry_json
    WHERE year = YEAR(CURRENT_DATE) 
      AND month = MONTH(CURRENT_DATE)
      AND day = DAY(CURRENT_DATE)
    GROUP BY hour
)
SELECT 
    'Latest Event Time' as metric,
    CAST(latest_event AS VARCHAR) as value
FROM recent_data
UNION ALL
SELECT 
    'Minutes Since Last Event' as metric,
    CAST(DATEDIFF('minute', latest_event, CURRENT_TIMESTAMP) AS VARCHAR) as value
FROM recent_data
UNION ALL
SELECT 
    'Today Total Events' as metric,
    CAST(total_events AS VARCHAR) as value
FROM recent_data
UNION ALL
SELECT 
    'Today Unique Users' as metric,
    CAST(unique_users AS VARCHAR) as value
FROM recent_data
UNION ALL
SELECT 
    'Current Hour Event Rate' as metric,
    CAST(COALESCE(MAX(events_per_hour), 0) AS VARCHAR) as value
FROM hourly_rate
WHERE hour = HOUR(CURRENT_TIME)
UNION ALL
SELECT 
    'Pipeline Status' as metric,
    CASE 
        WHEN DATEDIFF('minute', MAX(latest_event), CURRENT_TIMESTAMP) > 30 THEN 'DELAYED'
        WHEN DATEDIFF('minute', MAX(latest_event), CURRENT_TIMESTAMP) > 15 THEN 'WARNING'
        ELSE 'HEALTHY'
    END as value
FROM recent_data;
```

## 📊 Export Queries for Dashboards

### QuickSight/Tableau Ready Queries

#### Executive Dashboard Dataset
```sql
-- Comprehensive metrics for executive dashboard
CREATE OR REPLACE VIEW acme_telemetry.executive_dashboard AS
SELECT 
    DATE(event_timestamp) as date,
    hour,
    -- User metrics
    COUNT(DISTINCT customer_id) as unique_users,
    COUNT(DISTINCT session_id) as sessions,
    COUNT(DISTINCT title_id) as unique_titles,
    -- Engagement metrics
    AVG(completion_percentage) as avg_completion,
    SUM(watch_duration_seconds) / 3600.0 as total_hours_watched,
    AVG(watch_duration_seconds) / 60.0 as avg_session_minutes,
    -- Quality metrics
    AVG(bandwidth_mbps) as avg_bandwidth,
    AVG(buffering_events) as avg_buffering,
    SUM(error_count) as total_errors,
    -- Event distribution
    COUNT(CASE WHEN event_type = 'start' THEN 1 END) as starts,
    COUNT(CASE WHEN event_type = 'complete' THEN 1 END) as completions,
    COUNT(CASE WHEN event_type = 'pause' THEN 1 END) as pauses,
    COUNT(CASE WHEN event_type = 'resume' THEN 1 END) as resumes,
    COUNT(CASE WHEN event_type = 'stop' THEN 1 END) as stops,
    -- Device breakdown
    COUNT(CASE WHEN device_type = 'TV' THEN 1 END) as tv_events,
    COUNT(CASE WHEN device_type = 'Mobile' THEN 1 END) as mobile_events,
    COUNT(CASE WHEN device_type = 'Tablet' THEN 1 END) as tablet_events,
    COUNT(CASE WHEN device_type = 'Web' THEN 1 END) as web_events,
    -- Quality breakdown
    COUNT(CASE WHEN quality = '4K' THEN 1 END) as quality_4k,
    COUNT(CASE WHEN quality = 'HD' THEN 1 END) as quality_hd,
    COUNT(CASE WHEN quality = 'SD' THEN 1 END) as quality_sd
FROM acme_telemetry.video_telemetry_json
GROUP BY DATE(event_timestamp), hour;
```

## 💡 Query Optimization Tips

### Performance Best Practices

1. **Always use partition filters**
```sql
-- Good: Uses partitions
SELECT * FROM acme_telemetry.video_telemetry_json 
WHERE year = 2025 AND month = 8 AND day = 11;

-- Bad: Full table scan
SELECT * FROM acme_telemetry.video_telemetry_json;
```

2. **Project only needed columns**
```sql
-- Good: Specific columns
SELECT customer_id, event_type, completion_percentage 
FROM acme_telemetry.video_telemetry_json;

-- Bad: All columns
SELECT * FROM acme_telemetry.video_telemetry_json;
```

3. **Use approximate functions when possible**
```sql
-- For large datasets, use approximate functions
SELECT 
    approx_distinct(customer_id) as approx_unique_users,
    approx_percentile(bandwidth_mbps, 0.5) as median_bandwidth
FROM acme_telemetry.video_telemetry_json;
```

4. **Optimize JOIN operations**
```sql
-- Use broadcast joins for small dimension tables
SELECT /*+ BROADCAST(d) */ 
    f.*, d.dimension_name
FROM fact_table f
JOIN small_dimension d ON f.dim_id = d.id;
```

## 📚 Additional Resources

- [Athena SQL Reference](https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html)
- [Presto Functions Documentation](https://prestodb.io/docs/current/functions.html)
- [Query Performance Tuning](https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html)

---

**Note**: All queries assume the table `acme_telemetry.video_telemetry_json` with the schema defined in the setup documentation. Adjust table names and column references as needed for your environment.