import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import * as path from 'path';
import { Config } from '../config';

export interface LambdaConstructProps {
  table: dynamodb.Table;
}

export class LambdaConstruct extends Construct {
  public readonly listServers: lambda.Function;
  public readonly getServer: lambda.Function;
  public readonly createServer: lambda.Function;
  public readonly updateServer: lambda.Function;
  public readonly deleteServer: lambda.Function;
  public readonly getTools: lambda.Function;

  constructor(scope: Construct, id: string, props: LambdaConstructProps) {
    super(scope, id);

    const commonEnv = {
      TABLE_NAME: props.table.tableName,
      CATEGORY_INDEX: Config.dynamodb.categoryIndex,
      STATUS_INDEX: Config.dynamodb.statusIndex,
    };

    const commonProps: Partial<nodejs.NodejsFunctionProps> = {
      runtime: lambda.Runtime.NODEJS_20_X,
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      logRetention: logs.RetentionDays.ONE_WEEK,
      environment: commonEnv,
      bundling: {
        minify: true,
        sourceMap: true,
        externalModules: ['@aws-sdk/*'],
      },
    };

    const lambdaDir = path.join(__dirname, '..', '..', 'lambda');

    // List Servers
    this.listServers = new nodejs.NodejsFunction(this, 'ListServersFunction', {
      ...commonProps,
      entry: path.join(lambdaDir, 'list-servers', 'index.ts'),
      functionName: `${Config.naming.prefix}-list-servers`,
      description: 'List MCP servers from registry',
    });
    props.table.grantReadData(this.listServers);

    // Get Server
    this.getServer = new nodejs.NodejsFunction(this, 'GetServerFunction', {
      ...commonProps,
      entry: path.join(lambdaDir, 'get-server', 'index.ts'),
      functionName: `${Config.naming.prefix}-get-server`,
      description: 'Get MCP server details',
    });
    props.table.grantReadData(this.getServer);

    // Create Server
    this.createServer = new nodejs.NodejsFunction(this, 'CreateServerFunction', {
      ...commonProps,
      entry: path.join(lambdaDir, 'create-server', 'index.ts'),
      functionName: `${Config.naming.prefix}-create-server`,
      description: 'Register new MCP server',
    });
    props.table.grantWriteData(this.createServer);

    // Update Server
    this.updateServer = new nodejs.NodejsFunction(this, 'UpdateServerFunction', {
      ...commonProps,
      entry: path.join(lambdaDir, 'update-server', 'index.ts'),
      functionName: `${Config.naming.prefix}-update-server`,
      description: 'Update MCP server',
    });
    props.table.grantReadWriteData(this.updateServer);

    // Delete Server
    this.deleteServer = new nodejs.NodejsFunction(this, 'DeleteServerFunction', {
      ...commonProps,
      entry: path.join(lambdaDir, 'delete-server', 'index.ts'),
      functionName: `${Config.naming.prefix}-delete-server`,
      description: 'Delete MCP server from registry',
    });
    props.table.grantReadWriteData(this.deleteServer);

    // Get Tools - requires additional AgentCore and Secrets Manager permissions
    this.getTools = new nodejs.NodejsFunction(this, 'GetToolsFunction', {
      ...commonProps,
      entry: path.join(lambdaDir, 'get-tools', 'index.ts'),
      functionName: `${Config.naming.prefix}-get-tools`,
      description: 'Get/refresh MCP server tools',
      timeout: cdk.Duration.seconds(60),
      environment: {
        ...commonEnv,
        MCP_CREDENTIALS_SECRET: 'acme-chatbot/mcp-credentials',
      },
      bundling: {
        minify: true,
        sourceMap: true,
        externalModules: ['@aws-sdk/*'],
      },
    });
    props.table.grantReadWriteData(this.getTools);

    // Grant AgentCore permissions to getTools Lambda
    this.getTools.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock-agentcore:InvokeAgentRuntime',
        ],
        resources: ['*'],
      })
    );

    // Grant Secrets Manager read access for MCP credentials
    this.getTools.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'secretsmanager:GetSecretValue',
        ],
        resources: [
          `arn:aws:secretsmanager:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:secret:acme-chatbot/mcp-credentials*`,
        ],
      })
    );
  }
}
