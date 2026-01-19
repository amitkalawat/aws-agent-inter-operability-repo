# ACME Chat Frontend Infrastructure

AWS CDK infrastructure for deploying the ACME Chat React frontend to production using S3 + CloudFront with security best practices.

## 🏗️ Architecture

```
Users → CloudFront Distribution → Origin Access Identity → Private S3 Bucket
                ↓
            HTTPS Only + Caching + Compression + Error Handling
```

### 🔒 Security Features

- **Private S3 Bucket**: No public access, completely locked down
- **Origin Access Identity (OAI)**: Only CloudFront can access S3
- **HTTPS Enforcement**: All HTTP traffic redirected to HTTPS
- **No Direct S3 Access**: Users cannot access S3 URLs directly

### ⚡ Performance Features

- **Global CDN**: CloudFront edge locations worldwide
- **Compression**: Gzip and Brotli compression enabled
- **Optimized Caching**: Different cache policies for static vs dynamic content
- **Price Class 100**: Uses only North America and Europe edge locations

## 📋 Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Node.js** (v16 or higher)
3. **AWS CDK** installed globally: `npm install -g aws-cdk`

Required AWS permissions:
- S3 (create buckets, upload objects)
- CloudFront (create distributions)
- IAM (create roles for OAI)
- CloudFormation (deploy stacks)

## 🚀 Quick Start

### Initial Deployment

```bash
# Navigate to infrastructure directory
cd frontend/infrastructure

# Install dependencies
npm install

# Deploy everything (builds React app + deploys infrastructure)
npm run deploy
```

This will:
1. Build the React app for production
2. Create the CDK infrastructure
3. Upload the built files to S3
4. Configure CloudFront distribution
5. Output the public URL

### Future Updates

For subsequent deployments after making changes to the React app:

```bash
npm run deploy:update
```

This only rebuilds the React app and updates the deployment without recreating infrastructure.

## 📁 Project Structure

```
infrastructure/
├── lib/
│   └── infrastructure-stack.ts    # Main CDK stack definition
├── bin/
│   └── infrastructure.ts          # CDK app entry point
├── scripts/
│   └── deploy.sh                  # Deployment automation script
├── package.json                   # NPM scripts and dependencies
├── cdk.json                      # CDK configuration
└── README.md                     # This file
```

## 🛠 CDK Stack Components

### S3 Bucket (`AcmeChatWebsiteBucket`)
- **Private Access**: `blockPublicAccess: BLOCK_ALL`
- **No Public Reads**: `publicReadAccess: false`
- **Unique Name**: `acme-chat-frontend-{account-id}-{region}`
- **Auto-cleanup**: Configured for easy teardown

### CloudFront Distribution (`AcmeChatDistribution`)
- **OAI Integration**: Secure access to private S3 bucket
- **HTTPS Enforcement**: Redirects all HTTP to HTTPS
- **Error Handling**: 404/403 errors redirect to index.html (SPA support)
- **Compression**: Automatic Gzip/Brotli compression
- **Cache Policies**: Optimized for static assets and HTML files

### Origin Access Identity (`AcmeChatOAI`)
- **Secure Access**: Only CloudFront can read from S3
- **IAM Policy**: Grants `s3:GetObject` permission to OAI principal

### Deployment (`AcmeChatDeployment`)
- **Automated Upload**: Uploads React build files to S3
- **Cache Invalidation**: Invalidates CloudFront cache on deploy
- **Source**: Uses `../acme-chat/build` directory

## 📝 Available Commands

```bash
# Full deployment (first time or major changes)
npm run deploy

# Quick update (React app changes only)
npm run deploy:update

# Preview changes before deployment
npm run diff

# Generate CloudFormation template
npm run synth

# Destroy all infrastructure (careful!)
npm run destroy

# Build TypeScript
npm run build

# Watch for TypeScript changes
npm run watch
```

## 🌐 Outputs

After successful deployment, you'll get:

- **Distribution Domain Name**: `https://d1234567890123.cloudfront.net`
- **S3 Bucket Name**: `acme-chat-frontend-123456789-us-east-1`
- **Distribution ID**: `E1234567890ABC`

## 🧪 Testing the Deployment

1. **Visit the CloudFront URL** (provided in deployment output)
2. **Verify HTTPS**: Should automatically redirect from HTTP
3. **Test SPA Routing**: Refresh the page or navigate to `/login` - should work
4. **Login and Test**: Use demo credentials to test full functionality
5. **Check Security**: Try accessing S3 bucket URL directly - should fail

## 🔧 Configuration

### Cache Policies

**Default Behavior** (`/`):
- TTL: Managed by CloudFront's optimized policy
- Best for: HTML files, API responses

**Static Assets** (`/static/*`):
- Default TTL: 30 days
- Max TTL: 365 days
- Best for: JS, CSS, images, fonts

### Error Handling

- **403 Forbidden** → Redirect to `index.html` (for client-side routing)
- **404 Not Found** → Redirect to `index.html` (for client-side routing)
- **TTL**: 30 minutes (prevents over-caching errors)

## 🔍 Monitoring

Monitor your deployment:

1. **CloudFront Console**: View cache hit rates, request metrics
2. **S3 Console**: Check bucket contents and access logs
3. **CloudWatch**: Monitor CloudFront and S3 metrics
4. **Browser DevTools**: Check cache headers and load times

## 💰 Cost Optimization

- **Price Class 100**: Only uses US/Canada and Europe edge locations
- **Compression**: Reduces bandwidth costs
- **Efficient Caching**: Reduces origin requests
- **No Reserved Capacity**: Pay-as-you-go pricing

## 🚨 Security Best Practices

✅ **Implemented:**
- Private S3 bucket with blocked public access
- OAI for secure CloudFront→S3 access
- HTTPS enforcement
- No direct S3 access possible

⚠️ **Additional Considerations for Production:**
- Custom domain with SSL certificate
- WAF (Web Application Firewall)
- Security headers (CSP, HSTS, etc.)
- Access logging and monitoring

## 🔄 CI/CD Integration

This infrastructure is designed for easy CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Deploy Frontend
  run: |
    cd frontend/infrastructure
    npm ci
    npm run deploy:update
```

## 🧹 Cleanup

To remove all resources:

```bash
npm run destroy
```

**Warning**: This will delete the S3 bucket and all contents!

## 🐛 Troubleshooting

### Common Issues

1. **Deployment fails with permissions error**
   - Ensure AWS CLI is configured with proper permissions
   - Check IAM policies for S3, CloudFront, and CloudFormation

2. **React app shows blank page**
   - Check browser console for JavaScript errors
   - Verify build directory exists and contains files
   - Check CloudFront error pages configuration

3. **404 errors on page refresh**
   - This is expected for SPAs - the error handling should redirect to index.html
   - If not working, check CloudFront error response configuration

4. **Build takes a long time**
   - First deployment creates all resources (~10-15 minutes)
   - Subsequent updates are much faster (~2-3 minutes)

### Debug Commands

```bash
# Check what will be deployed
npm run diff

# Generate CloudFormation template for review
npm run synth

# Check CloudFront distribution status
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID

# List S3 bucket contents
aws s3 ls s3://your-bucket-name --recursive
```

---

**🎯 Result**: A secure, fast, and scalable React deployment on AWS with industry best practices!