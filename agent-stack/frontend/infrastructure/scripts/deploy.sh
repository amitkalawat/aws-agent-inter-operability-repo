#!/bin/bash

# ACME Chat Frontend Deployment Script
# This script builds the React app and deploys it to AWS using CDK

set -e  # Exit on any error

echo "🚀 ACME Chat Frontend Deployment"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "../acme-chat/package.json" ]; then
    echo "❌ Error: React app not found. Please run this script from the infrastructure directory."
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Error: AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account and region info
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

echo "📋 Deployment Info:"
echo "   AWS Account: $AWS_ACCOUNT_ID"
echo "   AWS Region: $AWS_REGION"
echo "   React App: ../acme-chat/"
echo ""

# Step 1: Build React app for production
echo "🔨 Step 1: Building React app for production..."
cd ../acme-chat
echo "   Installing/updating dependencies..."
npm ci

echo "   Building production bundle..."
npm run build

if [ ! -d "build" ]; then
    echo "❌ Error: Build directory not found. React build failed."
    exit 1
fi

echo "✅ React app built successfully!"
echo "   Build size: $(du -sh build | cut -f1)"
echo ""

# Step 2: Prepare CDK deployment
cd ../infrastructure
echo "🏗️ Step 2: Preparing CDK deployment..."
echo "   Installing CDK dependencies..."
npm ci

echo "   Compiling TypeScript..."
npm run build

# Step 3: Bootstrap CDK (if needed)
echo "🔧 Step 3: Checking CDK bootstrap..."
if ! cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION 2>/dev/null; then
    echo "   Bootstrapping CDK for first-time use..."
    cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION
fi

echo "✅ CDK ready for deployment!"
echo ""

# Step 4: Deploy the stack
echo "🚀 Step 4: Deploying infrastructure..."
echo "   This will create:"
echo "   • S3 bucket (private, no public access)"
echo "   • CloudFront distribution with OAI"
echo "   • Upload React build files"
echo "   • Configure caching and error handling"
echo ""

cdk deploy --require-approval never

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment successful!"
    echo ""
    echo "📊 What was created:"
    echo "   ✅ Private S3 bucket for hosting"
    echo "   ✅ CloudFront distribution with HTTPS"
    echo "   ✅ Origin Access Identity (OAI) for security"
    echo "   ✅ React app uploaded and cached"
    echo ""
    
    # Get the CloudFront URL
    DISTRIBUTION_URL=$(aws cloudformation describe-stacks \
        --stack-name InfrastructureStack \
        --query 'Stacks[0].Outputs[?OutputKey==`DistributionDomainName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$DISTRIBUTION_URL" ]; then
        echo "🌐 Your ACME Chat is now live at:"
        echo "   https://$DISTRIBUTION_URL"
        echo ""
        echo "🔒 Security features:"
        echo "   • S3 bucket is completely private"
        echo "   • Only CloudFront can access S3 via OAI"
        echo "   • HTTPS enforced (HTTP redirects to HTTPS)"
        echo "   • Optimized caching for performance"
        echo ""
        echo "⚡ Performance features:"
        echo "   • Gzip/Brotli compression enabled"
        echo "   • Static assets cached for 30 days"
        echo "   • SPA routing support (404→index.html)"
        echo ""
        echo "🧪 Test your deployment:"
        echo "   1. Visit: https://$DISTRIBUTION_URL"
        echo "   2. Login with: admin@acmecorp.com"
        echo "   3. Password: Admin@123456!"
        echo "   4. Start chatting with Claude!"
    fi
    
    echo ""
    echo "📝 Next steps:"
    echo "   • Update DNS if you have a custom domain"
    echo "   • Monitor CloudFront metrics in AWS Console"
    echo "   • Use 'npm run deploy:update' for future updates"
    
else
    echo "❌ Deployment failed. Check the error messages above."
    exit 1
fi