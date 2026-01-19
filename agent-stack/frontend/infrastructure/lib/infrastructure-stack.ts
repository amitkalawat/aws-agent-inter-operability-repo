import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as iam from 'aws-cdk-lib/aws-iam';
import { RemovalPolicy } from 'aws-cdk-lib';

export class InfrastructureStack extends cdk.Stack {
  public readonly distributionDomainName: string;
  public readonly bucketName: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create S3 bucket for hosting React app (private access only)
    const websiteBucket = new s3.Bucket(this, 'AcmeChatWebsiteBucket', {
      bucketName: `acme-chat-frontend-${cdk.Aws.ACCOUNT_ID}-${cdk.Aws.REGION}`,
      versioned: false,
      publicReadAccess: false, // Keep private
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL, // Block all public access
      removalPolicy: RemovalPolicy.DESTROY, // For demo purposes
      autoDeleteObjects: true, // For demo purposes
    });

    // Create Origin Access Identity for CloudFront to access S3
    const originAccessIdentity = new cloudfront.OriginAccessIdentity(
      this,
      'AcmeChatOAI',
      {
        comment: 'OAI for ACME Chat Frontend',
      }
    );

    // Grant CloudFront OAI read access to the S3 bucket
    websiteBucket.addToResourcePolicy(
      new iam.PolicyStatement({
        actions: ['s3:GetObject'],
        resources: [websiteBucket.arnForObjects('*')],
        principals: [originAccessIdentity.grantPrincipal],
      })
    );

    // Create CloudFront distribution
    const distribution = new cloudfront.Distribution(this, 'AcmeChatDistribution', {
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(30),
        },
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(30),
        },
      ],
      defaultBehavior: {
        origin: new origins.S3Origin(websiteBucket, {
          originAccessIdentity: originAccessIdentity,
        }),
        compress: true,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
      },
      additionalBehaviors: {
        // Cache static assets for longer
        '/static/*': {
          origin: new origins.S3Origin(websiteBucket, {
            originAccessIdentity: originAccessIdentity,
          }),
          compress: true,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: new cloudfront.CachePolicy(this, 'StaticAssetsCachePolicy', {
            cachePolicyName: 'acme-chat-static-assets',
            comment: 'Cache policy for static assets',
            defaultTtl: cdk.Duration.days(30),
            maxTtl: cdk.Duration.days(365),
            minTtl: cdk.Duration.seconds(0),
            enableAcceptEncodingBrotli: true,
            enableAcceptEncodingGzip: true,
          }),
        },
      },
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // Use only North America and Europe
      enabled: true,
      comment: 'ACME Chat Frontend Distribution',
    });

    // Deploy React build to S3
    new s3deploy.BucketDeployment(this, 'AcmeChatDeployment', {
      sources: [s3deploy.Source.asset('../acme-chat/build')],
      destinationBucket: websiteBucket,
      distribution: distribution,
      distributionPaths: ['/*'], // Invalidate all paths
    });

    // Output the CloudFront distribution URL
    new cdk.CfnOutput(this, 'DistributionDomainName', {
      value: distribution.distributionDomainName,
      description: 'CloudFront Distribution Domain Name',
      exportName: 'AcmeChatDistributionDomainName',
    });

    // Output the S3 bucket name
    new cdk.CfnOutput(this, 'S3BucketName', {
      value: websiteBucket.bucketName,
      description: 'S3 Bucket Name for Frontend Assets',
      exportName: 'AcmeChatS3BucketName',
    });

    // Output the CloudFront distribution ID
    new cdk.CfnOutput(this, 'DistributionId', {
      value: distribution.distributionId,
      description: 'CloudFront Distribution ID',
      exportName: 'AcmeChatDistributionId',
    });

    // Store values for access by other methods
    this.distributionDomainName = distribution.distributionDomainName;
    this.bucketName = websiteBucket.bucketName;
  }
}
