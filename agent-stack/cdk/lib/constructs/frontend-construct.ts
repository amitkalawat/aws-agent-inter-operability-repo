import * as path from 'path';
import { Construct } from 'constructs';
import {
  Aws,
  Duration,
  RemovalPolicy,
  CfnOutput,
} from 'aws-cdk-lib';
import {
  Bucket,
  BlockPublicAccess,
} from 'aws-cdk-lib/aws-s3';
import {
  Distribution,
  OriginAccessIdentity,
  AllowedMethods,
  ViewerProtocolPolicy,
  CachePolicy,
  OriginRequestPolicy,
  PriceClass,
} from 'aws-cdk-lib/aws-cloudfront';
import { S3Origin } from 'aws-cdk-lib/aws-cloudfront-origins';
import { BucketDeployment, Source } from 'aws-cdk-lib/aws-s3-deployment';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { IUserPool, IUserPoolClient } from 'aws-cdk-lib/aws-cognito';
import { Config } from '../config';

export interface FrontendConstructProps {
  readonly userPool: IUserPool;
  readonly frontendClient: IUserPoolClient;
  readonly agentRuntimeArn: string;
  readonly removalPolicy?: RemovalPolicy;
}

export class FrontendConstruct extends Construct {
  public readonly distribution: Distribution;
  public readonly bucket: Bucket;
  public readonly distributionUrl: string;

  constructor(scope: Construct, id: string, props: FrontendConstructProps) {
    super(scope, id);

    const removalPolicy = props.removalPolicy ?? RemovalPolicy.DESTROY;

    // Create S3 bucket for hosting React app (private access only)
    this.bucket = new Bucket(this, 'WebsiteBucket', {
      bucketName: `${Config.frontend.bucketNamePrefix}-${Aws.ACCOUNT_ID}-${Aws.REGION}`,
      versioned: false,
      publicReadAccess: false,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      removalPolicy: removalPolicy,
      autoDeleteObjects: removalPolicy === RemovalPolicy.DESTROY,
    });

    // Create Origin Access Identity for CloudFront to access S3
    const originAccessIdentity = new OriginAccessIdentity(this, 'OAI', {
      comment: 'OAI for ACME Chat Frontend',
    });

    // Grant CloudFront OAI read access to the S3 bucket
    this.bucket.addToResourcePolicy(
      new PolicyStatement({
        actions: ['s3:GetObject'],
        resources: [this.bucket.arnForObjects('*')],
        principals: [originAccessIdentity.grantPrincipal],
      })
    );

    // Create static assets cache policy
    const staticAssetsCachePolicy = new CachePolicy(this, 'StaticAssetsCachePolicy', {
      cachePolicyName: `${Config.naming.projectPrefix}-static-assets`,
      comment: 'Cache policy for static assets',
      defaultTtl: Duration.days(Config.frontend.cachePolicy.staticAssetsTtlDays),
      maxTtl: Duration.days(Config.frontend.cachePolicy.staticAssetsMaxTtlDays),
      minTtl: Duration.seconds(0),
      enableAcceptEncodingBrotli: true,
      enableAcceptEncodingGzip: true,
    });

    // Create CloudFront distribution
    this.distribution = new Distribution(this, 'Distribution', {
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: Duration.minutes(30),
        },
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: Duration.minutes(30),
        },
      ],
      defaultBehavior: {
        origin: new S3Origin(this.bucket, {
          originAccessIdentity: originAccessIdentity,
        }),
        compress: true,
        allowedMethods: AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        viewerProtocolPolicy: ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: CachePolicy.CACHING_OPTIMIZED,
        originRequestPolicy: OriginRequestPolicy.CORS_S3_ORIGIN,
      },
      additionalBehaviors: {
        '/static/*': {
          origin: new S3Origin(this.bucket, {
            originAccessIdentity: originAccessIdentity,
          }),
          compress: true,
          allowedMethods: AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          viewerProtocolPolicy: ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: staticAssetsCachePolicy,
        },
      },
      priceClass: PriceClass.PRICE_CLASS_100,
      enabled: true,
      comment: 'ACME Chat Frontend Distribution',
    });

    this.distributionUrl = `https://${this.distribution.distributionDomainName}`;

    // Deploy React build to S3
    const buildPath = path.join(__dirname, '../..', Config.frontend.buildPath);
    new BucketDeployment(this, 'Deployment', {
      sources: [Source.asset(buildPath)],
      destinationBucket: this.bucket,
      distribution: this.distribution,
      distributionPaths: ['/*'],
    });

    // Outputs
    new CfnOutput(this, 'DistributionDomainName', {
      value: this.distribution.distributionDomainName,
      description: 'CloudFront Distribution Domain Name',
      exportName: 'AcmeChatDistributionDomainName',
    });

    new CfnOutput(this, 'DistributionUrl', {
      value: this.distributionUrl,
      description: 'CloudFront Distribution URL',
      exportName: 'AcmeChatDistributionUrl',
    });

    new CfnOutput(this, 'S3BucketName', {
      value: this.bucket.bucketName,
      description: 'S3 Bucket Name for Frontend Assets',
      exportName: 'AcmeChatS3BucketName',
    });

    new CfnOutput(this, 'DistributionId', {
      value: this.distribution.distributionId,
      description: 'CloudFront Distribution ID',
      exportName: 'AcmeChatDistributionId',
    });

    // Output frontend configuration for reference
    new CfnOutput(this, 'FrontendConfig', {
      value: JSON.stringify({
        userPoolId: props.userPool.userPoolId,
        clientId: props.frontendClient.userPoolClientId,
        region: Config.aws.region,
        agentArn: props.agentRuntimeArn,
        agentEndpoint: `https://bedrock-agentcore.${Config.aws.region}.amazonaws.com`,
      }),
      description: 'Frontend configuration JSON',
      exportName: 'AcmeChatFrontendConfig',
    });
  }
}
