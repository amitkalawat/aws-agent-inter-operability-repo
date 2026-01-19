-- Sample Analytics Queries for Acme Corp Streaming Platform
-- These queries demonstrate cross-table analytics capabilities

-- ============================================
-- 1. VIEWER ENGAGEMENT METRICS
-- ============================================

-- Average watch time by subscription tier
SELECT 
    c.subscription_tier,
    COUNT(DISTINCT c.customer_id) as total_customers,
    COUNT(DISTINCT tel.customer_id) as active_viewers,
    ROUND(100.0 * COUNT(DISTINCT tel.customer_id) / COUNT(DISTINCT c.customer_id), 2) as engagement_rate,
    ROUND(AVG(tel.watch_duration_seconds) / 60.0, 2) as avg_watch_minutes,
    ROUND(AVG(tel.completion_percentage), 2) as avg_completion_rate
FROM customers c
LEFT JOIN telemetry tel ON c.customer_id = tel.customer_id
WHERE tel.event_timestamp >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY c.subscription_tier
ORDER BY engagement_rate DESC;

-- ============================================
-- 2. CONTENT PERFORMANCE ANALYSIS
-- ============================================

-- Top 20 most-watched titles with revenue impact
WITH viewing_stats AS (
    SELECT 
        t.title_id,
        t.title_name,
        t.genre,
        t.title_type,
        t.is_original,
        COUNT(DISTINCT tel.customer_id) as unique_viewers,
        COUNT(*) as total_views,
        SUM(tel.watch_duration_seconds) / 3600.0 as total_hours_watched,
        AVG(tel.completion_percentage) as avg_completion_rate
    FROM titles t
    JOIN telemetry tel ON t.title_id = tel.title_id
    WHERE tel.event_timestamp >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY t.title_id, t.title_name, t.genre, t.title_type, t.is_original
),
revenue_impact AS (
    SELECT 
        vs.*,
        COUNT(DISTINCT CASE WHEN c.subscription_tier != 'free_with_ads' THEN c.customer_id END) as paying_viewers,
        SUM(CASE WHEN c.subscription_tier != 'free_with_ads' THEN c.monthly_revenue ELSE 0 END) as monthly_revenue_impact
    FROM viewing_stats vs
    JOIN telemetry tel ON vs.title_id = tel.title_id
    JOIN customers c ON tel.customer_id = c.customer_id
    WHERE tel.event_timestamp >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY vs.title_id, vs.title_name, vs.genre, vs.title_type, vs.is_original, 
             vs.unique_viewers, vs.total_views, vs.total_hours_watched, vs.avg_completion_rate
)
SELECT * FROM revenue_impact
ORDER BY unique_viewers DESC
LIMIT 20;

-- ============================================
-- 3. AD CAMPAIGN EFFECTIVENESS
-- ============================================

-- Ad campaign performance correlated with viewing behavior
WITH ad_viewers AS (
    SELECT 
        c.customer_id,
        c.subscription_tier,
        c.preferred_genres,
        COUNT(DISTINCT tel.title_id) as titles_watched,
        SUM(tel.watch_duration_seconds) / 3600.0 as total_hours_watched
    FROM customers c
    JOIN telemetry tel ON c.customer_id = tel.customer_id
    WHERE c.subscription_tier = 'free_with_ads'
        AND tel.event_timestamp >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY c.customer_id, c.subscription_tier, c.preferred_genres
)
SELECT 
    camp.campaign_name,
    camp.advertiser_name,
    camp.campaign_type,
    camp.target_genres,
    camp.impressions,
    camp.clicks,
    camp.click_through_rate,
    camp.spent_amount,
    camp.cost_per_click,
    ROUND(camp.spent_amount / camp.impressions * 1000, 2) as effective_cpm
FROM campaigns camp
WHERE camp.status = 'active'
    AND camp.target_subscription_tiers LIKE '%free_with_ads%'
ORDER BY click_through_rate DESC
LIMIT 20;

-- ============================================
-- 4. CUSTOMER LIFETIME VALUE ANALYSIS
-- ============================================

-- Customer cohort analysis by acquisition channel
WITH customer_cohorts AS (
    SELECT 
        DATE_TRUNC('month', subscription_start_date) as cohort_month,
        acquisition_channel,
        subscription_tier,
        COUNT(*) as customers_acquired,
        COUNT(CASE WHEN is_active = true THEN 1 END) as customers_retained,
        AVG(lifetime_value) as avg_ltv,
        AVG(CASE WHEN is_active = false 
            THEN DATE_DIFF('day', subscription_start_date, subscription_end_date) 
            ELSE DATE_DIFF('day', subscription_start_date, CURRENT_DATE) 
        END) as avg_tenure_days
    FROM customers
    WHERE subscription_start_date >= CURRENT_DATE - INTERVAL '12' MONTH
    GROUP BY DATE_TRUNC('month', subscription_start_date), acquisition_channel, subscription_tier
)
SELECT 
    cohort_month,
    acquisition_channel,
    subscription_tier,
    customers_acquired,
    customers_retained,
    ROUND(100.0 * customers_retained / customers_acquired, 2) as retention_rate,
    ROUND(avg_ltv, 2) as avg_lifetime_value,
    ROUND(avg_tenure_days, 0) as avg_tenure_days
FROM customer_cohorts
ORDER BY cohort_month DESC, avg_lifetime_value DESC;

-- ============================================
-- 5. VIEWING PATTERNS AND DEVICE USAGE
-- ============================================

-- Peak viewing hours by device type
WITH hourly_views AS (
    SELECT 
        EXTRACT(HOUR FROM event_timestamp) as hour_of_day,
        device_type,
        COUNT(*) as view_count,
        COUNT(DISTINCT customer_id) as unique_viewers,
        AVG(watch_duration_seconds) / 60.0 as avg_watch_minutes
    FROM telemetry
    WHERE event_timestamp >= CURRENT_DATE - INTERVAL '7' DAY
        AND event_type IN ('stop', 'complete')
    GROUP BY EXTRACT(HOUR FROM event_timestamp), device_type
)
SELECT 
    hour_of_day,
    device_type,
    view_count,
    unique_viewers,
    ROUND(avg_watch_minutes, 2) as avg_watch_minutes,
    ROUND(100.0 * view_count / SUM(view_count) OVER (PARTITION BY hour_of_day), 2) as pct_of_hour
FROM hourly_views
ORDER BY hour_of_day, view_count DESC;

-- ============================================
-- 6. CONTENT DISCOVERY AND RECOMMENDATIONS
-- ============================================

-- Genre affinity analysis for personalization
WITH user_genre_views AS (
    SELECT 
        c.customer_id,
        c.preferred_genres,
        t.genre,
        COUNT(*) as views_in_genre,
        SUM(tel.watch_duration_seconds) / 3600.0 as hours_watched_in_genre
    FROM customers c
    JOIN telemetry tel ON c.customer_id = tel.customer_id
    JOIN titles t ON tel.title_id = t.title_id
    WHERE tel.event_timestamp >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY c.customer_id, c.preferred_genres, t.genre
),
genre_preferences AS (
    SELECT 
        customer_id,
        genre,
        views_in_genre,
        hours_watched_in_genre,
        RANK() OVER (PARTITION BY customer_id ORDER BY hours_watched_in_genre DESC) as genre_rank
    FROM user_genre_views
)
SELECT 
    genre,
    COUNT(DISTINCT CASE WHEN genre_rank = 1 THEN customer_id END) as top_genre_for_users,
    AVG(hours_watched_in_genre) as avg_hours_watched,
    COUNT(DISTINCT customer_id) as total_viewers
FROM genre_preferences
GROUP BY genre
ORDER BY top_genre_for_users DESC;

-- ============================================
-- 7. REVENUE OPTIMIZATION OPPORTUNITIES
-- ============================================

-- Identify upsell opportunities based on viewing behavior
WITH heavy_free_users AS (
    SELECT 
        c.customer_id,
        c.email,
        c.subscription_tier,
        COUNT(DISTINCT tel.title_id) as titles_watched,
        SUM(tel.watch_duration_seconds) / 3600.0 as total_hours,
        COUNT(DISTINCT DATE(tel.event_timestamp)) as active_days,
        MAX(tel.event_timestamp) as last_active
    FROM customers c
    JOIN telemetry tel ON c.customer_id = tel.customer_id
    WHERE c.subscription_tier = 'free_with_ads'
        AND c.is_active = true
        AND tel.event_timestamp >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY c.customer_id, c.email, c.subscription_tier
    HAVING SUM(tel.watch_duration_seconds) / 3600.0 > 20  -- More than 20 hours/month
)
SELECT 
    customer_id,
    email,
    titles_watched,
    ROUND(total_hours, 2) as total_hours_watched,
    active_days,
    last_active,
    8.99 * 12 as potential_annual_revenue  -- Basic tier annual revenue
FROM heavy_free_users
ORDER BY total_hours DESC
LIMIT 100;

-- ============================================
-- 8. CONTENT COST EFFICIENCY
-- ============================================

-- ROI analysis for licensed vs original content
WITH content_performance AS (
    SELECT 
        t.title_id,
        t.title_name,
        t.is_original,
        t.licensing_cost,
        t.budget_millions,
        COUNT(DISTINCT tel.customer_id) as unique_viewers,
        SUM(tel.watch_duration_seconds) / 3600.0 as total_hours_watched
    FROM titles t
    JOIN telemetry tel ON t.title_id = tel.title_id
    WHERE tel.event_timestamp >= CURRENT_DATE - INTERVAL '90' DAY
    GROUP BY t.title_id, t.title_name, t.is_original, t.licensing_cost, t.budget_millions
),
content_value AS (
    SELECT 
        cp.*,
        COUNT(DISTINCT c.customer_id) as paying_viewers,
        SUM(c.monthly_revenue) * 3 as revenue_generated  -- 3 months revenue attribution
    FROM content_performance cp
    JOIN telemetry tel ON cp.title_id = tel.title_id
    JOIN customers c ON tel.customer_id = c.customer_id
    WHERE c.subscription_tier != 'free_with_ads'
        AND tel.event_timestamp >= CURRENT_DATE - INTERVAL '90' DAY
    GROUP BY cp.title_id, cp.title_name, cp.is_original, cp.licensing_cost, 
             cp.budget_millions, cp.unique_viewers, cp.total_hours_watched
)
SELECT 
    title_name,
    is_original,
    unique_viewers,
    ROUND(total_hours_watched, 0) as total_hours,
    ROUND(CASE 
        WHEN is_original THEN budget_millions * 1000000
        ELSE licensing_cost * 1000000
    END, 0) as content_cost,
    ROUND(revenue_generated, 0) as revenue_generated,
    ROUND(revenue_generated - CASE 
        WHEN is_original THEN budget_millions * 1000000
        ELSE licensing_cost * 1000000
    END, 0) as net_value,
    ROUND(total_hours_watched / CASE 
        WHEN is_original THEN budget_millions
        ELSE licensing_cost
    END, 2) as hours_per_million_spent
FROM content_value
WHERE (is_original AND budget_millions > 0) OR (NOT is_original AND licensing_cost > 0)
ORDER BY net_value DESC
LIMIT 20;