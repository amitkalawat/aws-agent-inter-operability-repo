#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { McpRegistryStack } from '../lib/mcp-registry-stack';
import { Config } from '../lib/config';

const app = new cdk.App();

new McpRegistryStack(app, 'McpRegistryStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: Config.aws.region,
  },
  description: 'MCP Server Registry - Browse and manage MCP servers on Bedrock AgentCore',
});

app.synth();
