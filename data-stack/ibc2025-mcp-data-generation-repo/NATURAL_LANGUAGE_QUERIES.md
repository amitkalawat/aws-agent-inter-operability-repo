# Natural Language Queries for Acme Streaming Platform Analytics

This guide provides natural language questions that can be asked about the streaming platform data, organized by business use case. Each question can be translated into SQL queries using Amazon Athena.

## 📊 Customer Analytics Questions

### Subscription & Demographics
- "How many customers do we have in each subscription tier?"
- "What's the distribution of customers by age group?"
- "Which countries have the most premium subscribers?"
- "What percentage of our customers are active vs churned?"
- "What's the average lifetime value by subscription tier?"
- "How many customers joined in the last 30 days?"
- "What's the churn rate by acquisition channel?"
- "Which payment methods are most popular?"
- "What's the geographic distribution of our customer base?"
- "How many free-tier users could we potentially upsell to paid tiers?"

### Customer Behavior
- "Which age groups watch the most content?"
- "What are the preferred genres for each subscription tier?"
- "How long do customers typically stay subscribed?"
- "What's the average monthly revenue per customer?"
- "Which acquisition channels bring the highest-value customers?"
- "What percentage of free users convert to paid subscriptions?"
- "How does viewing behavior differ between subscription tiers?"

## 🎬 Content Performance Questions

### Title Analytics
- "What are the top 10 most-watched movies this month?"
- "Which TV series have the highest completion rates?"
- "What's the average popularity score by genre?"
- "How many original titles do we have vs licensed content?"
- "Which documentaries have won the most awards?"
- "What's the average budget for movies vs series?"
- "Which genres generate the most revenue?"
- "What percentage of our content is rated R vs PG-13?"
- "Which production studios create our most popular content?"
- "What's the ROI on original content vs licensed content?"

### Viewing Patterns
- "What are the peak viewing hours?"
- "How does viewing behavior differ by device type?"
- "What's the average watch duration by content type?"
- "Which titles have the highest re-watch rates?"
- "What percentage of users complete movies vs series episodes?"
- "How many hours of content are consumed daily?"
- "Which genres are most popular during weekends?"

## 📱 Device & Technology Questions

### Platform Usage
- "What's the device breakdown for our viewers (mobile vs TV vs web)?"
- "Which devices have the highest streaming quality usage?"
- "What's the average bandwidth consumption by device type?"
- "How many buffering events occur on average per session?"
- "Which ISPs provide the best streaming experience?"
- "What app versions are most commonly used?"
- "How does connection type (WiFi vs cellular) affect viewing duration?"
- "Which operating systems do our mobile users prefer?"

### Technical Performance
- "What's the average buffering duration per viewing session?"
- "Which regions experience the most streaming errors?"
- "How does video quality correlate with completion rates?"
- "What percentage of streams are in 4K vs HD vs SD?"
- "Which cities have the best streaming performance?"

## 💰 Revenue & Monetization Questions

### Revenue Analysis
- "What's our total monthly recurring revenue?"
- "How much revenue comes from each subscription tier?"
- "What's the average revenue per user (ARPU)?"
- "Which customer segments generate the most lifetime value?"
- "How has revenue grown month-over-month?"
- "What's the revenue impact of our top 20 titles?"
- "Which genres drive the most subscription upgrades?"

### Ad Campaign Performance
- "Which ad campaigns have the highest click-through rates?"
- "What's the cost per acquisition for each campaign?"
- "Which advertisers spend the most on our platform?"
- "How effective are video ads vs display ads?"
- "What's the ROI on campaigns targeting specific age groups?"
- "Which industries advertise most on our platform?"
- "What's the average CPM (cost per thousand impressions)?"
- "How many conversions do our ad campaigns generate?"

## 📈 Business Intelligence Questions

### Growth Metrics
- "What's our month-over-month subscriber growth rate?"
- "How many new titles were added this quarter?"
- "What's the customer acquisition cost trend?"
- "Which markets are growing fastest?"
- "What's our market penetration by country?"

### Engagement Metrics
- "What's the average engagement rate by subscription tier?"
- "How many unique viewers do we have daily/weekly/monthly?"
- "What percentage of customers are highly engaged (>20 hours/month)?"
- "What's the average number of titles watched per customer?"
- "How many customers haven't watched anything in 30 days?"

### Content Strategy
- "Which genres should we invest more in based on viewing trends?"
- "What types of content have the best cost-to-engagement ratio?"
- "Should we produce more series or movies based on completion rates?"
- "Which content ratings perform best with our audience?"
- "What's the optimal episode length for maximum engagement?"

## 🎯 Targeted Analysis Questions

### Cohort Analysis
- "How does retention differ for customers acquired in different months?"
- "What's the viewing behavior of our newest cohort vs oldest?"
- "Which cohort has the highest lifetime value?"
- "How do holiday season cohorts perform vs regular months?"

### Segmentation Questions
- "Who are our power users (top 10% by watch time)?"
- "Which customers are at risk of churning?"
- "What defines our most valuable customer segment?"
- "How can we segment customers for personalized recommendations?"
- "Which segments respond best to email marketing?"

### Predictive Analytics Questions
- "Which free users are most likely to upgrade?"
- "What factors predict customer churn?"
- "Which content will likely perform well based on historical data?"
- "What's the predicted lifetime value for new customers?"
- "When are customers most likely to cancel their subscription?"

## 🔍 Competitive Analysis Questions

- "How does our content library size compare to competitors?"
- "What's our average content budget vs industry standards?"
- "How do our subscription prices compare to market rates?"
- "What percentage of viewing time goes to original vs licensed content?"
- "How diverse is our content library by genre and language?"

## 📊 Sample Complex Queries

### Multi-dimensional Analysis
- "Show me the top 10 series by completion rate, broken down by age group and subscription tier"
- "What's the correlation between content budget and viewer engagement?"
- "How does time of day affect viewing patterns across different device types and genres?"
- "Which combination of genre, rating, and duration maximizes viewer retention?"
- "What's the revenue per viewing hour for each content type?"

### Time-based Trending
- "How have viewing patterns changed over the last 6 months?"
- "What's the seasonal trend in subscription sign-ups?"
- "Which genres are gaining or losing popularity?"
- "How does weekend viewing compare to weekday viewing?"
- "What's the trend in average session duration?"

## 🚀 Actionable Insights Questions

### Optimization Opportunities
- "Which underperforming content should we consider removing?"
- "What's the optimal ad frequency for free-tier users?"
- "Which markets have untapped potential based on low penetration?"
- "What content gaps exist in our library based on user preferences?"
- "How can we optimize content recommendations to increase watch time?"

### Business Decisions
- "Should we introduce a new subscription tier based on usage patterns?"
- "Which original series should get renewed based on performance?"
- "What's the business case for expanding into new geographic markets?"
- "How much should we invest in 4K content based on usage?"
- "Which partnership opportunities make sense based on our user base?"

## 📝 Notes on Using These Queries

1. **Time Ranges**: Most queries can be modified with different time ranges (last 7 days, 30 days, quarter, year)
2. **Granularity**: Results can be grouped by various dimensions (daily, weekly, monthly)
3. **Filters**: Add filters for specific segments, regions, or content types
4. **Comparisons**: Many queries can be enhanced with period-over-period comparisons
5. **Thresholds**: Adjust thresholds based on business requirements (e.g., "heavy users" = >20 hours/month)

## 🔗 Related Documentation

- See `scripts/sample_queries.sql` for SQL implementations
- Review `DATA_TYPE_NOTES.md` for understanding data types and schema
- Check `README.md` for data model descriptions

## 💡 Tips for Query Optimization

1. **Use partitions**: Telemetry data is partitioned by date for faster queries
2. **Limit time ranges**: Restrict queries to necessary time periods
3. **Aggregate first**: Perform aggregations before joins when possible
4. **Use sampling**: For exploratory analysis, consider sampling large datasets
5. **Cache results**: Frequently-used queries can be saved as views