import { Construct } from 'constructs';
import { RemovalPolicy, CfnOutput } from 'aws-cdk-lib';
import { Secret, ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { IUserPool, IUserPoolClient } from 'aws-cdk-lib/aws-cognito';
import { Config } from '../config';

export interface SecretsConstructProps {
  readonly userPool: IUserPool;
  readonly mcpClient: IUserPoolClient;
  readonly cognitoDomain: string;
  readonly removalPolicy?: RemovalPolicy;
}

export class SecretsConstruct extends Construct {
  public readonly mcpCredentials: ISecret;

  constructor(scope: Construct, id: string, props: SecretsConstructProps) {
    super(scope, id);

    const removalPolicy = props.removalPolicy ?? RemovalPolicy.DESTROY;

    // Create secret for MCP credentials
    // Note: The MCP client secret needs to be retrieved after stack deployment
    // and stored in this secret along with other MCP configuration
    this.mcpCredentials = new Secret(this, 'McpCredentials', {
      secretName: Config.secrets.mcpCredentialsName,
      description: 'MCP Server credentials for ACME chatbot',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          MCP_COGNITO_POOL_ID: props.userPool.userPoolId,
          MCP_COGNITO_REGION: Config.aws.region,
          MCP_COGNITO_CLIENT_ID: props.mcpClient.userPoolClientId,
          MCP_COGNITO_DOMAIN: props.cognitoDomain,
        }),
        generateStringKey: 'MCP_COGNITO_CLIENT_SECRET',
      },
      removalPolicy: removalPolicy,
    });

    // Output
    new CfnOutput(this, 'McpCredentialsArn', {
      value: this.mcpCredentials.secretArn,
      description: 'MCP Credentials Secret ARN',
      exportName: 'AcmeMcpCredentialsArn',
    });

    new CfnOutput(this, 'McpCredentialsName', {
      value: this.mcpCredentials.secretName,
      description: 'MCP Credentials Secret Name',
      exportName: 'AcmeMcpCredentialsName',
    });
  }
}
