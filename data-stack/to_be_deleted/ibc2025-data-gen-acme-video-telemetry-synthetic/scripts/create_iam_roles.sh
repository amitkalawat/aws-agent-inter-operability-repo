#!/bin/bash

# Create IAM Roles for ACME Telemetry Pipeline
# Usage: ./create_iam_roles.sh

set -e

echo "🔐 Creating IAM Roles for ACME Telemetry Pipeline..."

# Configuration
REGION="eu-central-1"
ACCOUNT_ID="241533163649"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create trust policy document
cat > /tmp/lambda-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# 1. Create Generator Role
echo -e "${YELLOW}Creating Generator Role...${NC}"
aws iam create-role \
  --role-name AcmeTelemetry-Generator-Role \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --region $REGION 2>/dev/null || echo "Role already exists"

# Attach policies to Generator Role
aws iam attach-role-policy \
  --role-name AcmeTelemetry-Generator-Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --region $REGION

# Create custom policy for Generator
cat > /tmp/generator-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:AcmeTelemetry-Producer",
        "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:AcmeTelemetry-DataLoader"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name AcmeTelemetry-Generator-Role \
  --policy-name GeneratorInvokePolicy \
  --policy-document file:///tmp/generator-policy.json \
  --region $REGION

echo -e "${GREEN}✅ Generator Role created${NC}"

# 2. Create Producer Role
echo -e "${YELLOW}Creating Producer Role...${NC}"
aws iam create-role \
  --role-name AcmeTelemetry-Producer-Role \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --region $REGION 2>/dev/null || echo "Role already exists"

# Attach policies to Producer Role
aws iam attach-role-policy \
  --role-name AcmeTelemetry-Producer-Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole \
  --region $REGION

# Create custom policy for Producer
cat > /tmp/producer-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kafka-cluster:Connect",
        "kafka-cluster:DescribeCluster"
      ],
      "Resource": "arn:aws:kafka:${REGION}:${ACCOUNT_ID}:cluster/*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kafka-cluster:ReadData",
        "kafka-cluster:WriteData",
        "kafka-cluster:DescribeTopic",
        "kafka-cluster:CreateTopic",
        "kafka-cluster:AlterTopic"
      ],
      "Resource": "arn:aws:kafka:${REGION}:${ACCOUNT_ID}:topic/*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kafka-cluster:AlterGroup",
        "kafka-cluster:DescribeGroup"
      ],
      "Resource": "arn:aws:kafka:${REGION}:${ACCOUNT_ID}:group/*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kafka:DescribeCluster",
        "kafka:GetBootstrapBrokers"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name AcmeTelemetry-Producer-Role \
  --policy-name ProducerMSKPolicy \
  --policy-document file:///tmp/producer-policy.json \
  --region $REGION

echo -e "${GREEN}✅ Producer Role created${NC}"

# 3. Create Data Loader Role
echo -e "${YELLOW}Creating Data Loader Role...${NC}"
aws iam create-role \
  --role-name AcmeTelemetry-DataLoader-Role \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --region $REGION 2>/dev/null || echo "Role already exists"

# Attach policies to Data Loader Role
aws iam attach-role-policy \
  --role-name AcmeTelemetry-DataLoader-Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --region $REGION

# Create custom policy for Data Loader
cat > /tmp/data-loader-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StopQueryExecution"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetPartitions"
      ],
      "Resource": [
        "arn:aws:glue:${REGION}:${ACCOUNT_ID}:catalog",
        "arn:aws:glue:${REGION}:${ACCOUNT_ID}:database/acme_streaming_data",
        "arn:aws:glue:${REGION}:${ACCOUNT_ID}:table/acme_streaming_data/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::acme-telemetry-${ACCOUNT_ID}-${REGION}/*",
        "arn:aws:s3:::acme-telemetry-${ACCOUNT_ID}-${REGION}",
        "arn:aws:s3:::acme-streaming-data-lake-${ACCOUNT_ID}-${REGION}/*",
        "arn:aws:s3:::acme-streaming-data-lake-${ACCOUNT_ID}-${REGION}"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name AcmeTelemetry-DataLoader-Role \
  --policy-name DataLoaderPolicy \
  --policy-document file:///tmp/data-loader-policy.json \
  --region $REGION

echo -e "${GREEN}✅ Data Loader Role created${NC}"

# 4. Create Firehose Role
echo -e "${YELLOW}Creating Firehose Role...${NC}"

cat > /tmp/firehose-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "firehose.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name AcmeTelemetry-Firehose-Role \
  --assume-role-policy-document file:///tmp/firehose-trust-policy.json \
  --region $REGION 2>/dev/null || echo "Role already exists"

# Create custom policy for Firehose
cat > /tmp/firehose-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:AbortMultipartUpload",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::acme-telemetry-${ACCOUNT_ID}-${REGION}",
        "arn:aws:s3:::acme-telemetry-${ACCOUNT_ID}-${REGION}/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kafka:DescribeCluster",
        "kafka:GetBootstrapBrokers",
        "kafka-cluster:Connect",
        "kafka-cluster:DescribeCluster",
        "kafka-cluster:ReadData",
        "kafka-cluster:DescribeTopic"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name AcmeTelemetry-Firehose-Role \
  --policy-name FirehosePolicy \
  --policy-document file:///tmp/firehose-policy.json \
  --region $REGION

echo -e "${GREEN}✅ Firehose Role created${NC}"

# 5. Create Glue Crawler Role
echo -e "${YELLOW}Creating Glue Crawler Role...${NC}"

cat > /tmp/glue-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name AcmeTelemetry-GlueCrawler-Role \
  --assume-role-policy-document file:///tmp/glue-trust-policy.json \
  --region $REGION 2>/dev/null || echo "Role already exists"

# Attach policies to Glue Crawler Role
aws iam attach-role-policy \
  --role-name AcmeTelemetry-GlueCrawler-Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole \
  --region $REGION

# Create custom policy for Glue Crawler
cat > /tmp/glue-crawler-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::acme-telemetry-${ACCOUNT_ID}-${REGION}",
        "arn:aws:s3:::acme-telemetry-${ACCOUNT_ID}-${REGION}/*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name AcmeTelemetry-GlueCrawler-Role \
  --policy-name GlueCrawlerS3Policy \
  --policy-document file:///tmp/glue-crawler-policy.json \
  --region $REGION

echo -e "${GREEN}✅ Glue Crawler Role created${NC}"

# Clean up temporary files
rm -f /tmp/lambda-trust-policy.json
rm -f /tmp/generator-policy.json
rm -f /tmp/producer-policy.json
rm -f /tmp/data-loader-policy.json
rm -f /tmp/firehose-trust-policy.json
rm -f /tmp/firehose-policy.json
rm -f /tmp/glue-trust-policy.json
rm -f /tmp/glue-crawler-policy.json

echo -e "${GREEN}🎉 All IAM roles created successfully!${NC}"
echo ""
echo "Roles created:"
echo "  - AcmeTelemetry-Generator-Role"
echo "  - AcmeTelemetry-Producer-Role"
echo "  - AcmeTelemetry-DataLoader-Role"
echo "  - AcmeTelemetry-Firehose-Role"
echo "  - AcmeTelemetry-GlueCrawler-Role"