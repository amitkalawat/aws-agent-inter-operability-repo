import { Construct } from 'constructs';
import { CfnOutput, RemovalPolicy, Stack, CustomResource, Duration } from 'aws-cdk-lib';
import { IUserPool, IUserPoolClient } from 'aws-cdk-lib/aws-cognito';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import {
  Gateway,
  GatewayTarget,
  McpProtocolConfiguration,
  GatewayAuthorizerConfiguration,
  OAuth2CredentialProvider,
  SearchType,
} from '@aws-cdk/aws-bedrock-agentcore-alpha';
import {
  PolicyStatement,
  Effect,
  Role,
  ServicePrincipal,
  ManagedPolicy,
} from 'aws-cdk-lib/aws-iam';
import { Runtime as LambdaRuntime, Code, Function } from 'aws-cdk-lib/aws-lambda';
import { Provider } from 'aws-cdk-lib/custom-resources';
import { Config } from '../config';

export interface McpServerInfo {
  readonly name: string;
  readonly runtimeArn: string;
}

export interface GatewayConstructProps {
  readonly userPool: IUserPool;
  readonly frontendClient: IUserPoolClient;
  readonly mcpClient: IUserPoolClient;
  readonly mcpCredentials: ISecret;
  readonly mcpServers: McpServerInfo[];
  readonly cognitoDomain: string;
  readonly removalPolicy?: RemovalPolicy;
}

/**
 * AgentCore Gateway Construct
 *
 * Creates a unified MCP Gateway that aggregates multiple MCP servers behind
 * a single endpoint. This simplifies agent code by:
 * - Providing a single connection point instead of N connections
 * - Enabling semantic tool discovery across all MCP servers
 * - Centralizing authentication management
 *
 * Architecture:
 *   Agent → Gateway (single endpoint) → MCP Server 1
 *                                    → MCP Server 2
 *                                    → ...
 */
export class GatewayConstruct extends Construct {
  public readonly gateway: Gateway;
  public readonly gatewayEndpoint: string;

  constructor(scope: Construct, id: string, props: GatewayConstructProps) {
    super(scope, id);

    const region = Stack.of(this).region;
    const account = Stack.of(this).account;
    const removalPolicy = props.removalPolicy ?? RemovalPolicy.DESTROY;

    // Build the discovery URL for Cognito OIDC
    const discoveryUrl = `https://cognito-idp.${region}.amazonaws.com/${props.userPool.userPoolId}/.well-known/openid-configuration`;

    // ========================================
    // 1. Create Gateway Service Role
    // ========================================
    const gatewayRole = new Role(this, 'GatewayRole', {
      assumedBy: new ServicePrincipal('bedrock-agentcore.amazonaws.com'),
      description: 'IAM role for ACME MCP Gateway',
    });

    // Grant permissions to invoke MCP server runtimes
    gatewayRole.addToPolicy(new PolicyStatement({
      effect: Effect.ALLOW,
      actions: [
        'bedrock-agentcore:InvokeRuntime',
      ],
      resources: props.mcpServers.map(s => s.runtimeArn),
    }));

    // Grant permissions for Gateway operations
    gatewayRole.addToPolicy(new PolicyStatement({
      effect: Effect.ALLOW,
      actions: [
        'bedrock-agentcore:CreateGateway',
        'bedrock-agentcore:GetGateway',
        'bedrock-agentcore:CreateGatewayTarget',
        'bedrock-agentcore:GetGatewayTarget',
        'bedrock-agentcore:UpdateGatewayTarget',
        'bedrock-agentcore:SynchronizeGatewayTargets',
        'bedrock-agentcore:ListGatewayTargets',
      ],
      resources: ['*'],
    }));

    // Grant read access to secrets for outbound OAuth
    props.mcpCredentials.grantRead(gatewayRole);

    // ========================================
    // 2. Create OAuth2 Credential Provider for Outbound Auth
    // ========================================
    // This provider supplies OAuth tokens for Gateway→MCP server communication
    const mcpCredentialProvider = new OAuth2CredentialProvider(this, 'McpCredentialProvider', {
      name: `${Config.gateway.name}-oauth-provider`,
      oAuthDiscoveryEndpoint: `https://${props.cognitoDomain}/.well-known/openid-configuration`,
      clientId: props.mcpClient.userPoolClientId,
      clientSecretSecretArn: props.mcpCredentials.secretArn,
    });

    // ========================================
    // 3. Create the Gateway
    // ========================================
    this.gateway = new Gateway(this, 'McpGateway', {
      gatewayName: Config.gateway.name,
      description: Config.gateway.description,
      role: gatewayRole,

      // Inbound auth: Custom JWT validation using Cognito
      authorizerConfiguration: GatewayAuthorizerConfiguration.customJwt({
        allowedClients: [props.frontendClient.userPoolClientId],
        discoveryUrl: discoveryUrl,
      }),

      // MCP protocol configuration with semantic search
      protocolConfiguration: McpProtocolConfiguration.mcp({
        searchType: Config.gateway.searchType === 'SEMANTIC'
          ? SearchType.SEMANTIC
          : SearchType.NONE,
        supportedVersions: Config.gateway.mcpVersions,
      }),
    });

    // Apply removal policy
    this.gateway.applyRemovalPolicy(removalPolicy);

    // ========================================
    // 4. Add MCP Servers as Gateway Targets
    // ========================================
    for (const server of props.mcpServers) {
      // Build the MCP server endpoint URL
      const encodedArn = server.runtimeArn.replace(/:/g, '%3A').replace(/\//g, '%2F');
      const mcpEndpoint = `https://bedrock-agentcore.${region}.amazonaws.com/runtimes/${encodedArn}/invocations?qualifier=DEFAULT`;

      const target = new GatewayTarget(this, `${server.name}Target`, {
        targetName: server.name,
        gateway: this.gateway,

        // MCP server configuration
        mcpServerConfiguration: {
          endpoint: mcpEndpoint,
        },

        // Outbound OAuth credentials for MCP server authentication
        credentialProviderConfigurations: [{
          credentialProviderType: 'OAUTH',
          credentialProvider: {
            oauthCredentialProvider: {
              providerArn: mcpCredentialProvider.credentialProviderArn,
              scopes: ['mcp/invoke'],
            },
          },
        }],
      });

      // Ensure target depends on gateway
      target.node.addDependency(this.gateway);
    }

    // ========================================
    // 5. Store Gateway Endpoint
    // ========================================
    this.gatewayEndpoint = this.gateway.gatewayEndpoint;

    // ========================================
    // 6. Outputs
    // ========================================
    new CfnOutput(this, 'GatewayArn', {
      value: this.gateway.gatewayArn,
      description: 'MCP Gateway ARN',
      exportName: 'AcmeMcpGatewayArn',
    });

    new CfnOutput(this, 'GatewayEndpoint', {
      value: this.gatewayEndpoint,
      description: 'MCP Gateway Endpoint URL (use this for agent connections)',
      exportName: 'AcmeMcpGatewayEndpoint',
    });

    new CfnOutput(this, 'GatewayName', {
      value: Config.gateway.name,
      description: 'MCP Gateway Name',
      exportName: 'AcmeMcpGatewayName',
    });
  }
}
