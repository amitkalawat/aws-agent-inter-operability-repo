import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import * as path from 'path';
import { Config } from '../config';

export interface DatabaseConstructProps {
  mcpServerArns: {
    awsDocs: string;
    dataproc: string;
    rekognition: string;
    novaCanvas: string;
  };
}

export class DatabaseConstruct extends Construct {
  public readonly table: dynamodb.Table;

  constructor(scope: Construct, id: string, props: DatabaseConstructProps) {
    super(scope, id);

    // DynamoDB table for MCP servers
    this.table = new dynamodb.Table(this, 'ServersTable', {
      tableName: Config.dynamodb.tableName,
      partitionKey: {
        name: 'serverId',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      pointInTimeRecovery: true,
    });

    // GSI for category queries
    this.table.addGlobalSecondaryIndex({
      indexName: Config.dynamodb.categoryIndex,
      partitionKey: {
        name: 'category',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'createdAt',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI for status queries
    this.table.addGlobalSecondaryIndex({
      indexName: Config.dynamodb.statusIndex,
      partitionKey: {
        name: 'status',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Seed data Lambda - using NodejsFunction for proper bundling
    const seedLambda = new nodejs.NodejsFunction(this, 'SeedDataFunction', {
      runtime: lambda.Runtime.NODEJS_20_X,
      entry: path.join(__dirname, '..', '..', 'lambda', 'seed-data', 'index.ts'),
      handler: 'handler',
      timeout: cdk.Duration.minutes(1),
      memorySize: 256,
      environment: {
        TABLE_NAME: this.table.tableName,
        AWS_DOCS_MCP_ARN: props.mcpServerArns.awsDocs,
        DATAPROC_MCP_ARN: props.mcpServerArns.dataproc,
        REKOGNITION_MCP_ARN: props.mcpServerArns.rekognition,
        NOVA_CANVAS_MCP_ARN: props.mcpServerArns.novaCanvas,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
      bundling: {
        minify: true,
        sourceMap: true,
        externalModules: ['@aws-sdk/*'],
      },
    });

    this.table.grantWriteData(seedLambda);
    this.table.grantReadData(seedLambda);

    // Custom resource to run seed on deploy
    const seedProvider = new cr.Provider(this, 'SeedProvider', {
      onEventHandler: seedLambda,
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    new cdk.CustomResource(this, 'SeedData', {
      serviceToken: seedProvider.serviceToken,
      properties: {
        // Force re-seed on each deploy if ARNs change
        awsDocsArn: props.mcpServerArns.awsDocs,
        dataprocArn: props.mcpServerArns.dataproc,
        rekognitionArn: props.mcpServerArns.rekognition,
        novaCanvasArn: props.mcpServerArns.novaCanvas,
        timestamp: Date.now().toString(),
      },
    });
  }
}
