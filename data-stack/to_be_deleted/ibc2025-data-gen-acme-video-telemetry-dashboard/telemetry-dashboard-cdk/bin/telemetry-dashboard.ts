#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { TelemetryDashboardStack } from '../lib/telemetry-dashboard-stack';

const app = new cdk.App();

// Get configuration from context or environment variables
const mskClusterArn = app.node.tryGetContext('mskClusterArn') || process.env.MSK_CLUSTER_ARN;
const mskSecurityGroupId = app.node.tryGetContext('mskSecurityGroupId') || process.env.MSK_SECURITY_GROUP_ID;
const vpcId = app.node.tryGetContext('vpcId') || process.env.VPC_ID;
const privateSubnetIds = (app.node.tryGetContext('privateSubnetIds') || process.env.PRIVATE_SUBNET_IDS || '').split(',').filter((id: string) => id);

// Validate required parameters
if (!mskClusterArn) {
  throw new Error('MSK_CLUSTER_ARN is required. Set it as an environment variable or pass via -c mskClusterArn=...');
}

if (!mskSecurityGroupId) {
  throw new Error('MSK_SECURITY_GROUP_ID is required. Set it as an environment variable or pass via -c mskSecurityGroupId=...');
}

if (!vpcId) {
  throw new Error('VPC_ID is required. Set it as an environment variable or pass via -c vpcId=...');
}

if (privateSubnetIds.length === 0) {
  throw new Error('PRIVATE_SUBNET_IDS is required. Set it as an environment variable or pass via -c privateSubnetIds=...');
}

new TelemetryDashboardStack(app, 'TelemetryDashboardStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1'
  },
  mskClusterArn,
  mskSecurityGroupId,
  vpcId,
  privateSubnetIds,
  description: 'Video Telemetry Dashboard with MSK integration and WebSocket streaming'
});

app.synth();