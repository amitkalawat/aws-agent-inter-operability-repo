#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { MskToS3Stack } from '../lib/msk-to-s3-stack';

const app = new cdk.App();

const vpcId = app.node.tryGetContext('vpcId');
const region = app.node.tryGetContext('region') || process.env.CDK_DEFAULT_REGION || 'us-east-1';
const account = app.node.tryGetContext('account') || process.env.CDK_DEFAULT_ACCOUNT;

if (!vpcId) {
  throw new Error('VPC ID is required. Please provide it using -c vpcId=<vpc-id>');
}

new MskToS3Stack(app, 'MskToS3Stack', {
  env: {
    account: account,
    region: region,
  },
  vpcId: vpcId,
  description: 'MSK cluster with S3 storage for logs and data',
  stackName: `MskToS3Stack-${region}`,
});