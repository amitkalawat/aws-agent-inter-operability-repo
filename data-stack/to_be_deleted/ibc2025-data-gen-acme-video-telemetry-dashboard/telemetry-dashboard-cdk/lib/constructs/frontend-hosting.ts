import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as cdk from 'aws-cdk-lib';
import * as path from 'path';
import * as fs from 'fs';

export interface FrontendHostingProps {
  userPoolId: string;
  userPoolClientId: string;
  webSocketUrl: string;
  region: string;
}

export class FrontendHosting extends Construct {
  public readonly distributionUrl: string;

  constructor(scope: Construct, id: string, props: FrontendHostingProps) {
    super(scope, id);

    // S3 bucket for frontend
    const bucket = new s3.Bucket(this, 'FrontendBucket', {
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'index.html',
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      bucketName: `telemetry-dashboard-frontend-${cdk.Stack.of(this).account}-${cdk.Stack.of(this).region}`
    });

    // CloudFront Origin Access Identity
    const originAccessIdentity = new cloudfront.OriginAccessIdentity(this, 'OAI', {
      comment: 'OAI for Telemetry Dashboard'
    });

    // Grant CloudFront access to S3 bucket
    bucket.grantRead(originAccessIdentity);

    // CloudFront distribution
    const distribution = new cloudfront.Distribution(this, 'Distribution', {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessIdentity(bucket, {
          originAccessIdentity
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
        compress: true
      },
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.seconds(0)
        },
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.seconds(0)
        }
      ],
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100
    });

    // Check if frontend build exists, if not create a placeholder
    const frontendBuildPath = path.join(__dirname, '../../frontend/build');
    if (!fs.existsSync(frontendBuildPath)) {
      // Create placeholder build directory
      fs.mkdirSync(path.join(__dirname, '../../frontend'), { recursive: true });
      fs.mkdirSync(frontendBuildPath, { recursive: true });
      
      // Create a placeholder index.html
      const placeholderHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telemetry Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        h1 {
            margin-bottom: 1rem;
        }
        .config {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9rem;
        }
        .config div {
            margin: 0.5rem 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Telemetry Dashboard</h1>
        <p>Frontend application will be deployed here.</p>
        <div class="config">
            <div>User Pool ID: ${props.userPoolId}</div>
            <div>Client ID: ${props.userPoolClientId}</div>
            <div>WebSocket URL: ${props.webSocketUrl}</div>
            <div>Region: ${props.region}</div>
        </div>
        <p style="margin-top: 2rem; opacity: 0.8;">
            Build your React app and redeploy to see the dashboard.
        </p>
    </div>
</body>
</html>`;
      
      fs.writeFileSync(path.join(frontendBuildPath, 'index.html'), placeholderHtml);
    }

    // Deploy frontend
    new s3deploy.BucketDeployment(this, 'DeployFrontend', {
      sources: [s3deploy.Source.asset(frontendBuildPath)],
      destinationBucket: bucket,
      distribution,
      distributionPaths: ['/*']
    });

    this.distributionUrl = `https://${distribution.distributionDomainName}`;
  }
}