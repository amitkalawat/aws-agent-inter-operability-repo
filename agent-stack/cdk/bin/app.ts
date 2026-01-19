#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { AcmeAgentCoreStack } from '../lib/acme-stack';
import { Config } from '../lib/config';

const app = new cdk.App();

// Create the main ACME AgentCore stack
new AcmeAgentCoreStack(app, Config.naming.stackName, {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: Config.aws.region,
  },
  description: 'ACME Corp Bedrock AgentCore Stack - Complete chatbot infrastructure with Cognito, MCP servers, and React frontend',
  developmentMode: true, // Set to false for production deployments
});

app.synth();
