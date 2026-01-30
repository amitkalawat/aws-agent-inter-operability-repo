#!/bin/bash
# Deploy frontend to S3 and invalidate CloudFront cache
# Usage: ./scripts/deploy-frontend.sh [stack-name] [region]

STACK_NAME=${1:-AcmeAgentCoreStack}
REGION=${2:-us-west-2}

echo "Fetching deployment targets from CloudFormation stack: $STACK_NAME"

# Get S3 bucket name
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketNameC6E6DF48`].OutputValue' \
  --output text 2>/dev/null)

# Get CloudFront distribution ID
DIST_ID=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendDistributionId6CBC2EDF`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$BUCKET" ] || [ "$BUCKET" == "None" ]; then
  echo "Error: Could not find S3 bucket. Make sure the stack is deployed."
  exit 1
fi

if [ -z "$DIST_ID" ] || [ "$DIST_ID" == "None" ]; then
  echo "Error: Could not find CloudFront distribution ID. Make sure the stack is deployed."
  exit 1
fi

echo "S3 Bucket: $BUCKET"
echo "CloudFront Distribution: $DIST_ID"

# Check if build directory exists
if [ ! -d "build" ]; then
  echo "Error: build/ directory not found. Run 'npm run build' first."
  exit 1
fi

# Sync to S3
echo ""
echo "Syncing build/ to s3://$BUCKET..."
aws s3 sync build "s3://$BUCKET" --delete --region "$REGION"

if [ $? -ne 0 ]; then
  echo "Error: S3 sync failed"
  exit 1
fi

# Invalidate CloudFront cache
echo ""
echo "Invalidating CloudFront cache..."
INVALIDATION=$(aws cloudfront create-invalidation \
  --distribution-id "$DIST_ID" \
  --paths "/*" \
  --region "$REGION" \
  --query 'Invalidation.[Id,Status]' \
  --output text)

echo "Invalidation: $INVALIDATION"

# Get frontend URL
FRONTEND_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendUrl`].OutputValue' \
  --output text 2>/dev/null)

echo ""
echo "✅ Frontend deployed successfully!"
echo "URL: $FRONTEND_URL"
echo ""
echo "Note: CloudFront invalidation may take 1-2 minutes to complete."
