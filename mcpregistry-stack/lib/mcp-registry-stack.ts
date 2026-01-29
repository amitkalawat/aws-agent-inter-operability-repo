import * as cdk from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';
import { DatabaseConstruct } from './constructs/database-construct';
import { LambdaConstruct } from './constructs/lambda-construct';
import { ApiConstruct } from './constructs/api-construct';
import { FrontendConstruct } from './constructs/frontend-construct';
import { Config } from './config';

export class McpRegistryStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Import Cognito User Pool from agent-stack
    const userPoolId = cdk.Fn.importValue(Config.imports.userPoolId);
    const userPool = cognito.UserPool.fromUserPoolId(
      this,
      'ImportedUserPool',
      userPoolId
    );

    // Import MCP server ARNs from agent-stack
    const mcpServerArns = {
      awsDocs: cdk.Fn.importValue(Config.imports.awsDocsMcpArn),
      dataproc: cdk.Fn.importValue(Config.imports.dataprocMcpArn),
      rekognition: cdk.Fn.importValue(Config.imports.rekognitionMcpArn),
      novaCanvas: cdk.Fn.importValue(Config.imports.novaCanvasMcpArn),
    };

    // Database construct (DynamoDB + seed data)
    const database = new DatabaseConstruct(this, 'Database', {
      mcpServerArns,
    });

    // Lambda functions construct
    const lambdas = new LambdaConstruct(this, 'Lambdas', {
      table: database.table,
    });

    // API Gateway construct with Cognito authorizer
    const api = new ApiConstruct(this, 'Api', {
      userPool,
      lambdas: {
        listServers: lambdas.listServers,
        getServer: lambdas.getServer,
        createServer: lambdas.createServer,
        updateServer: lambdas.updateServer,
        deleteServer: lambdas.deleteServer,
        getTools: lambdas.getTools,
      },
    });

    // Frontend construct (S3 + CloudFront)
    const frontend = new FrontendConstruct(this, 'Frontend', {
      api: api.api,
    });

    // Stack outputs
    new cdk.CfnOutput(this, 'UserPoolId', {
      value: userPoolId,
      description: 'Cognito User Pool ID (from agent-stack)',
    });

    new cdk.CfnOutput(this, 'FrontendClientId', {
      value: cdk.Fn.importValue(Config.imports.frontendClientId),
      description: 'Cognito Frontend Client ID (from agent-stack)',
    });

    new cdk.CfnOutput(this, 'TableName', {
      value: database.table.tableName,
      description: 'DynamoDB Table Name',
    });
  }
}
