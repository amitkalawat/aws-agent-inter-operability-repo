# Acme Corp Streaming Platform - Synthetic Data Generation & Analytics

This project generates synthetic data for a subscription-based video streaming platform (similar to Netflix) and provides AWS infrastructure for analytics using Glue, Athena, and Redshift.

## 📊 Overview

The system generates four main datasets that mirror a real streaming platform:
1. **Customer/Subscriber Data** - User demographics, subscription tiers, and preferences
2. **Title/Content Data** - Movies, series, and documentaries with metadata
3. **Video Telemetry Data** - Viewing events, watch duration, and device information
4. **Ad Campaign Data** - Advertising campaigns targeting free-tier users

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- AWS Account with appropriate permissions
- AWS CLI configured
- Node.js 14+ (for CDK)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd acme-streaming-data

# Install Python dependencies
pip install -r requirements.txt

# Install CDK dependencies
cd cdk
pip install -r requirements.txt
npm install -g aws-cdk
cd ..
```

### Generate Synthetic Data

```bash
# Generate default dataset (100K customers, 10K titles, 10M events)
python data_generation/main.py

# Custom generation
python data_generation/main.py --customers 50000 --titles 5000 --telemetry 5000000 --campaigns 250

# View all options
python data_generation/main.py --help
```

### Deploy AWS Infrastructure

```bash
# Navigate to CDK directory
cd cdk

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all stacks
cdk deploy --all

# Or deploy individual stacks
cdk deploy AcmeStreamingData-DataLake
cdk deploy AcmeStreamingData-Glue
cdk deploy AcmeStreamingData-Analytics
```

### Upload Data to S3

```bash
# Upload generated data to S3
python scripts/upload_to_s3.py --bucket <your-bucket-name>

# With custom options
python scripts/upload_to_s3.py --bucket <bucket> --local-dir output --s3-prefix raw
```

## 📁 Project Structure

```
acme-streaming-data/
├── data_generation/          # Data generation modules
│   ├── generators/          # Individual data generators
│   │   ├── customer_generator.py
│   │   ├── title_generator.py
│   │   ├── telemetry_generator.py
│   │   └── campaign_generator.py
│   ├── schemas/             # Data schemas
│   │   └── table_schemas.py
│   └── main.py             # Main generation script
├── cdk/                    # AWS CDK infrastructure
│   ├── stacks/
│   │   ├── data_lake_stack.py    # S3 bucket setup
│   │   ├── glue_stack.py         # Glue catalog
│   │   └── analytics_stack.py    # Athena & Redshift
│   ├── app.py              # CDK app entry point
│   └── requirements.txt
├── scripts/
│   ├── upload_to_s3.py     # S3 upload utility
│   └── sample_queries.sql  # Example analytics queries
├── output/                 # Generated data (git-ignored)
└── README.md
```

## 📊 Data Schemas

### Customer Table
- Demographics (age, location, etc.)
- Subscription information (tier, dates, revenue)
- Preferences and behavior patterns
- Acquisition and retention metrics

### Title Table
- Content metadata (name, type, genre, rating)
- Production information (country, language, cast)
- Performance metrics (ratings, popularity)
- Financial data (budget, revenue, licensing)

### Telemetry Table
- Viewing events with timestamps
- Watch duration and completion rates
- Device and quality information
- Network and performance metrics

### Campaign Table
- Campaign configuration and targeting
- Budget and spending information
- Performance metrics (impressions, clicks, conversions)
- ROI calculations

## 🔍 Analytics Capabilities

The infrastructure supports various analytics use cases:

1. **Customer Analytics**
   - Churn prediction and analysis
   - Lifetime value calculations
   - Segmentation and cohort analysis

2. **Content Performance**
   - Popular content by genre/demographic
   - Content ROI analysis
   - Viewing pattern insights

3. **Ad Campaign Effectiveness**
   - Campaign performance metrics
   - Targeting effectiveness
   - Revenue attribution

4. **Operational Insights**
   - Peak usage patterns
   - Device and quality preferences
   - Geographic distribution

## 🛠️ AWS Services Used

- **S3**: Data lake storage with lifecycle policies
- **Glue**: Data catalog and ETL capabilities
- **Athena**: Serverless SQL queries
- **Redshift Serverless**: Advanced analytics and BI
- **IAM**: Secure access management
- **VPC**: Network isolation for Redshift

## 📝 Sample Queries

See `scripts/sample_queries.sql` for example queries including:
- Viewer engagement by subscription tier
- Content performance with revenue impact
- Ad campaign ROI analysis
- Customer lifetime value by cohort
- Peak viewing patterns
- Upsell opportunity identification

## 🔐 Security Considerations

- All S3 buckets use encryption at rest
- IAM roles follow least-privilege principle
- VPC isolation for Redshift
- No hardcoded credentials
- Data anonymization in generated datasets

## 💰 Cost Optimization

- S3 lifecycle policies for data archival
- Redshift Serverless for pay-per-use
- Athena query result caching
- Partitioned data for efficient queries

## 🚀 Next Steps

1. **Run Glue Crawlers**: Update the data catalog after uploading data
2. **Create Athena Views**: Build reusable views for common queries
3. **Set Up QuickSight**: Create dashboards for visualization
4. **Implement ETL Jobs**: Process raw data into optimized formats
5. **Add Real-time Analytics**: Integrate Kinesis for streaming data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.