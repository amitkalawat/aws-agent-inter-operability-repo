import * as path from 'path';
import { Construct } from 'constructs';
import { Aws, CfnOutput, Duration, RemovalPolicy } from 'aws-cdk-lib';
import { IUserPool, IUserPoolClient } from 'aws-cdk-lib/aws-cognito';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { Bucket, BlockPublicAccess, BucketEncryption } from 'aws-cdk-lib/aws-s3';
import {
  Runtime,
  AgentRuntimeArtifact,
  RuntimeAuthorizerConfiguration,
  RuntimeNetworkConfiguration,
  ProtocolType,
} from '@aws-cdk/aws-bedrock-agentcore-alpha';
import {
  PolicyStatement,
  Effect,
} from 'aws-cdk-lib/aws-iam';
import { Config } from '../config';

export interface McpServerConfig {
  readonly name: string;
  readonly dockerPath: string;
  readonly description?: string;
  readonly additionalPolicies?: PolicyStatement[];
  readonly environmentVariables?: Record<string, string>;
}

export interface McpServerConstructProps {
  readonly userPool: IUserPool;
  readonly mcpClient: IUserPoolClient;
  readonly mcpCredentials: ISecret;
  readonly removalPolicy?: RemovalPolicy;
}

export interface McpServerRuntime {
  readonly runtime: Runtime;
  readonly name: string;
}

export class McpServerConstruct extends Construct {
  public readonly runtimes: Map<string, McpServerRuntime> = new Map();
  public readonly novaCanvasImageBucket: Bucket;

  constructor(scope: Construct, id: string, props: McpServerConstructProps) {
    super(scope, id);

    // Create S3 bucket for Nova Canvas generated images
    this.novaCanvasImageBucket = new Bucket(this, 'NovaCanvasImageBucket', {
      bucketName: `${Config.mcpServers.novaCanvas.imageBucketPrefix}-${Aws.ACCOUNT_ID}`,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      encryption: BucketEncryption.S3_MANAGED,
      removalPolicy: props.removalPolicy ?? RemovalPolicy.DESTROY,
      autoDeleteObjects: (props.removalPolicy ?? RemovalPolicy.DESTROY) === RemovalPolicy.DESTROY,
      lifecycleRules: [
        {
          id: 'ExpireGeneratedImages',
          expiration: Duration.days(Config.mcpServers.novaCanvas.imageExpirationDays),
          prefix: 'generated/',
        },
        {
          id: 'ExpireVisualizations',
          expiration: Duration.days(Config.mcpServers.novaCanvas.imageExpirationDays),
          prefix: 'visualizations/',
        },
      ],
    });

    // Define all MCP servers to deploy
    const mcpServers: McpServerConfig[] = [
      {
        name: Config.mcpServers.awsDocs.name,
        dockerPath: Config.mcpServers.awsDocs.dockerPath,
        description: 'AWS Documentation search MCP server',
      },
      {
        name: Config.mcpServers.dataProcessing.name,
        dockerPath: Config.mcpServers.dataProcessing.dockerPath,
        description: 'Data processing MCP server (Athena, Glue, EMR)',
        additionalPolicies: [
          new PolicyStatement({
            effect: Effect.ALLOW,
            actions: [
              // Athena query execution
              'athena:StartQueryExecution',
              'athena:GetQueryExecution',
              'athena:GetQueryResults',
              'athena:StopQueryExecution',
              'athena:GetWorkGroup',
              // Athena catalog/database/table listing
              'athena:ListDataCatalogs',
              'athena:ListDatabases',
              'athena:ListTableMetadata',
              'athena:GetDataCatalog',
              'athena:GetDatabase',
              'athena:GetTableMetadata',
              // Glue Data Catalog access (Athena uses Glue as metadata store)
              'glue:GetDatabase',
              'glue:GetDatabases',
              'glue:GetTable',
              'glue:GetTables',
              'glue:GetPartition',
              'glue:GetPartitions',
              'glue:BatchGetPartition',
              'glue:GetCatalogImportStatus',
              'glue:SearchTables',
              // S3 access for query results
              's3:GetObject',
              's3:PutObject',
              's3:ListBucket',
              's3:GetBucketLocation',
            ],
            resources: ['*'],
          }),
        ],
      },
      {
        name: Config.mcpServers.rekognition.name,
        dockerPath: Config.mcpServers.rekognition.dockerPath,
        description: 'Amazon Rekognition image analysis MCP server',
        additionalPolicies: [
          new PolicyStatement({
            effect: Effect.ALLOW,
            actions: [
              'rekognition:DetectLabels',
              'rekognition:DetectText',
              'rekognition:DetectFaces',
              'rekognition:RecognizeCelebrities',
              'rekognition:DetectModerationLabels',
              's3:GetObject',
            ],
            resources: ['*'],
          }),
        ],
      },
      {
        name: Config.mcpServers.novaCanvas.name,
        dockerPath: Config.mcpServers.novaCanvas.dockerPath,
        description: 'Amazon Nova Canvas image generation MCP server',
        environmentVariables: {
          IMAGE_OUTPUT_BUCKET: this.novaCanvasImageBucket.bucketName,
          // Nova Canvas is only available in us-east-1, ap-northeast-1, eu-west-1
          BEDROCK_REGION: 'us-east-1',
        },
        additionalPolicies: [
          new PolicyStatement({
            effect: Effect.ALLOW,
            actions: [
              'bedrock:InvokeModel',
            ],
            resources: [
              // Nova Canvas is only available in us-east-1, so we need cross-region access
              'arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-canvas-v1:0',
            ],
          }),
          new PolicyStatement({
            effect: Effect.ALLOW,
            actions: [
              's3:PutObject',
              's3:GetObject',
            ],
            resources: [
              this.novaCanvasImageBucket.bucketArn,
              `${this.novaCanvasImageBucket.bucketArn}/*`,
            ],
          }),
        ],
      },
    ];

    // Create each MCP server runtime
    for (const server of mcpServers) {
      const runtime = this.createMcpServer(server, props);
      this.runtimes.set(server.name, {
        runtime,
        name: server.name,
      });
    }
  }

  private createMcpServer(
    config: McpServerConfig,
    props: McpServerConstructProps
  ): Runtime {
    const dockerPath = path.join(__dirname, '../..', config.dockerPath);

    // Create the runtime artifact from Docker context
    const artifact = AgentRuntimeArtifact.fromAsset(dockerPath);

    // Create the MCP server runtime
    const runtime = new Runtime(this, `${config.name}Runtime`, {
      runtimeName: config.name,
      agentRuntimeArtifact: artifact,
      authorizerConfiguration: RuntimeAuthorizerConfiguration.usingCognito(
        props.userPool,
        [props.mcpClient]
      ),
      networkConfiguration: RuntimeNetworkConfiguration.usingPublicNetwork(),
      protocolConfiguration: ProtocolType.MCP,
      environmentVariables: {
        AWS_REGION: Config.aws.region,
        MCP_SERVER_NAME: config.name,
        ...config.environmentVariables,
      },
    });

    // Grant read access to MCP credentials secret
    props.mcpCredentials.grantRead(runtime);

    // Add additional policies if specified
    if (config.additionalPolicies) {
      for (const policy of config.additionalPolicies) {
        runtime.addToRolePolicy(policy);
      }
    }

    // Add CloudWatch Logs permissions
    runtime.addToRolePolicy(
      new PolicyStatement({
        effect: Effect.ALLOW,
        actions: [
          'logs:CreateLogGroup',
          'logs:CreateLogStream',
          'logs:PutLogEvents',
        ],
        resources: [
          `arn:aws:logs:${Config.aws.region}:*:log-group:/aws/bedrock-agentcore/runtimes/${config.name}*`,
        ],
      })
    );

    // Output
    new CfnOutput(this, `${config.name}Arn`, {
      value: runtime.agentRuntimeArn,
      description: `${config.name} MCP Server Runtime ARN`,
      exportName: `Acme${this.toPascalCase(config.name)}Arn`,
    });

    return runtime;
  }

  private toPascalCase(str: string): string {
    return str
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join('');
  }

  /**
   * Get all MCP server ARNs as a map
   */
  public getArns(): Record<string, string> {
    const arns: Record<string, string> = {};
    for (const [name, server] of this.runtimes) {
      arns[name] = server.runtime.agentRuntimeArn;
    }
    return arns;
  }
}
