import { Construct } from 'constructs';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as apigatewayv2_integrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import * as path from 'path';

export interface WebSocketApiProps {
  connectionsTable: dynamodb.Table;
  userPool: cognito.UserPool;
}

export class WebSocketApi extends Construct {
  public readonly webSocketApi: apigatewayv2.WebSocketApi;
  public readonly webSocketUrl: string;

  constructor(scope: Construct, id: string, props: WebSocketApiProps) {
    super(scope, id);

    // Lambda handlers
    const connectHandler = new lambda.Function(this, 'ConnectHandler', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'connect.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend/lambdas/websocket')),
      environment: {
        CONNECTIONS_TABLE: props.connectionsTable.tableName
      },
      timeout: cdk.Duration.seconds(10)
    });

    const disconnectHandler = new lambda.Function(this, 'DisconnectHandler', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'disconnect.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend/lambdas/websocket')),
      environment: {
        CONNECTIONS_TABLE: props.connectionsTable.tableName
      },
      timeout: cdk.Duration.seconds(10)
    });

    const defaultHandler = new lambda.Function(this, 'DefaultHandler', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'default.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend/lambdas/websocket')),
      timeout: cdk.Duration.seconds(10)
    });

    // Authorizer
    const authorizer = new lambda.Function(this, 'Authorizer', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'wsAuthorizer.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend/lambdas/authorizer')),
      environment: {
        USER_POOL_ID: props.userPool.userPoolId,
        REGION: cdk.Stack.of(this).region
      },
      timeout: cdk.Duration.seconds(10)
    });

    // Grant permissions
    props.connectionsTable.grantReadWriteData(connectHandler);
    props.connectionsTable.grantReadWriteData(disconnectHandler);

    // WebSocket API
    this.webSocketApi = new apigatewayv2.WebSocketApi(this, 'WebSocketApi', {
      apiName: 'telemetry-dashboard-ws',
      connectRouteOptions: {
        integration: new apigatewayv2_integrations.WebSocketLambdaIntegration(
          'ConnectIntegration',
          connectHandler
        ),
      },
      disconnectRouteOptions: {
        integration: new apigatewayv2_integrations.WebSocketLambdaIntegration(
          'DisconnectIntegration',
          disconnectHandler
        ),
      },
      defaultRouteOptions: {
        integration: new apigatewayv2_integrations.WebSocketLambdaIntegration(
          'DefaultIntegration',
          defaultHandler
        ),
      }
    });

    // Stage
    const stage = new apigatewayv2.WebSocketStage(this, 'Stage', {
      webSocketApi: this.webSocketApi,
      stageName: 'prod',
      autoDeploy: true
    });

    this.webSocketUrl = stage.url;
  }
}