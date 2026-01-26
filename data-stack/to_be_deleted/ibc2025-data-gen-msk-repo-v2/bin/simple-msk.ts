#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { SimpleMskStack } from '../lib/simple-msk-stack';

const app = new cdk.App();

const vpcId = app.node.tryGetContext('vpcId');
const region = app.node.tryGetContext('region') || process.env.CDK_DEFAULT_REGION || 'us-west-2';
const account = app.node.tryGetContext('account') || process.env.CDK_DEFAULT_ACCOUNT;

if (!vpcId) {
  throw new Error('VPC ID is required. Please provide it using -c vpcId=<vpc-id>');
}

new SimpleMskStack(app, 'SimpleMskStack', {
  env: {
    account: account,
    region: region,
  },
  vpcId: vpcId,
  description: 'Simple MSK cluster for Kafka streaming',
  stackName: `SimpleMskStack-${region}`,
});