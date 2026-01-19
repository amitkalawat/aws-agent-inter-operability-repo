import { Construct } from 'constructs';
import {
  Stack,
  StackProps,
  Tags,
  RemovalPolicy,
  CfnOutput,
} from 'aws-cdk-lib';
import { CognitoConstruct } from './constructs/cognito-construct';
import { SecretsConstruct } from './constructs/secrets-construct';
import { MemoryConstruct } from './constructs/memory-construct';
import { McpServerConstruct } from './constructs/mcp-server-construct';
import { AgentRuntimeConstruct } from './constructs/agent-runtime-construct';
import { FrontendConstruct } from './constructs/frontend-construct';
import { Config } from './config';

export interface AcmeAgentCoreStackProps extends StackProps {
  /**
   * Whether to deploy in development mode (DESTROY removal policy)
   * @default true
   */
  readonly developmentMode?: boolean;
}

/**
 * ACME Corp AgentCore Stack
 *
 * This stack deploys the complete ACME chatbot infrastructure:
 * - Cognito User Pool for authentication
 * - Secrets Manager for MCP credentials
 * - AgentCore Memory for conversation persistence
 * - MCP Servers (AWS Docs, DataProcessing, Rekognition, Nova Canvas)
 * - Main Agent Runtime (Strands + Claude Haiku 4.5)
 * - Frontend (React app on S3 + CloudFront)
 */
export class AcmeAgentCoreStack extends Stack {
  public readonly frontendUrl: string;
  public readonly agentArn: string;
  public readonly userPoolId: string;
  public readonly frontendClientId: string;

  constructor(scope: Construct, id: string, props?: AcmeAgentCoreStackProps) {
    super(scope, id, {
      ...props,
      env: props?.env ?? {
        region: Config.aws.region,
      },
    });

    const developmentMode = props?.developmentMode ?? true;
    const removalPolicy = developmentMode ? RemovalPolicy.DESTROY : RemovalPolicy.RETAIN;

    // Apply tags to all resources
    for (const [key, value] of Object.entries(Config.tags)) {
      Tags.of(this).add(key, value);
    }

    // ========================================
    // 1. Authentication Layer (Cognito)
    // ========================================
    const auth = new CognitoConstruct(this, 'Auth', {
      removalPolicy,
    });

    // ========================================
    // 2. Secrets Manager (MCP Credentials)
    // ========================================
    const secrets = new SecretsConstruct(this, 'Secrets', {
      userPool: auth.userPool,
      mcpClient: auth.mcpClient,
      removalPolicy,
    });

    // ========================================
    // 3. AgentCore Memory
    // ========================================
    const memory = new MemoryConstruct(this, 'Memory', {
      removalPolicy,
    });

    // ========================================
    // 4. MCP Servers
    // ========================================
    const mcpServers = new McpServerConstruct(this, 'McpServers', {
      userPool: auth.userPool,
      mcpClient: auth.mcpClient,
      mcpCredentials: secrets.mcpCredentials,
      removalPolicy,
    });

    // ========================================
    // 5. Main Agent Runtime
    // ========================================
    const agent = new AgentRuntimeConstruct(this, 'Agent', {
      userPool: auth.userPool,
      frontendClient: auth.frontendClient,
      mcpCredentials: secrets.mcpCredentials,
      memory: memory.memory,
      mcpServerEndpoints: mcpServers.getArns(),
      removalPolicy,
    });

    // ========================================
    // 6. Frontend (S3 + CloudFront)
    // ========================================
    const frontend = new FrontendConstruct(this, 'Frontend', {
      userPool: auth.userPool,
      frontendClient: auth.frontendClient,
      agentRuntimeArn: agent.runtime.agentRuntimeArn,
      removalPolicy,
    });

    // ========================================
    // Store public properties
    // ========================================
    this.frontendUrl = frontend.distributionUrl;
    this.agentArn = agent.runtime.agentRuntimeArn;
    this.userPoolId = auth.userPool.userPoolId;
    this.frontendClientId = auth.frontendClient.userPoolClientId;

    // ========================================
    // Stack-level outputs
    // ========================================
    new CfnOutput(this, 'FrontendUrl', {
      value: this.frontendUrl,
      description: 'ACME Chat Frontend URL',
      exportName: 'AcmeFrontendUrl',
    });

    new CfnOutput(this, 'AgentArn', {
      value: this.agentArn,
      description: 'Main Agent Runtime ARN',
      exportName: 'AcmeMainAgentArn',
    });

    new CfnOutput(this, 'CognitoUserPoolId', {
      value: this.userPoolId,
      description: 'Cognito User Pool ID',
      exportName: 'AcmeCognitoUserPoolId',
    });

    new CfnOutput(this, 'CognitoAppClientId', {
      value: this.frontendClientId,
      description: 'Cognito Frontend App Client ID',
      exportName: 'AcmeCognitoAppClientId',
    });

    new CfnOutput(this, 'DiscoveryUrl', {
      value: auth.discoveryUrl,
      description: 'Cognito OIDC Discovery URL',
      exportName: 'AcmeCognitoDiscoveryUrl',
    });

    new CfnOutput(this, 'MemoryId', {
      value: memory.memory.memoryId,
      description: 'AgentCore Memory ID',
      exportName: 'AcmeAgentCoreMemoryId',
    });

    // Output deployment summary
    new CfnOutput(this, 'DeploymentSummary', {
      value: JSON.stringify({
        region: Config.aws.region,
        stack: Config.naming.stackName,
        frontendUrl: this.frontendUrl,
        agentArn: this.agentArn,
        userPoolId: this.userPoolId,
        mcpServers: Object.keys(mcpServers.getArns()),
      }, null, 2),
      description: 'Deployment summary JSON',
    });
  }
}
