import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { CognitoAuth } from './constructs/cognito-auth';
import { WebSocketApi } from './constructs/websocket-api';
import { MskConsumer } from './constructs/msk-consumer';
import { FrontendHosting } from './constructs/frontend-hosting';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export interface TelemetryDashboardStackProps extends cdk.StackProps {
  mskClusterArn: string;
  mskSecurityGroupId: string;
  vpcId: string;
  privateSubnetIds: string[];
}

export class TelemetryDashboardStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: TelemetryDashboardStackProps) {
    super(scope, id, props);

    // DynamoDB table for WebSocket connections
    const connectionsTable = new dynamodb.Table(this, 'ConnectionsTable', {
      tableName: 'telemetry-connections',
      partitionKey: { name: 'connectionId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl'
    });

    // Cognito authentication
    const cognitoAuth = new CognitoAuth(this, 'CognitoAuth');

    // WebSocket API
    const webSocketApi = new WebSocketApi(this, 'WebSocketApi', {
      connectionsTable,
      userPool: cognitoAuth.userPool
    });

    // MSK Consumer
    const mskConsumer = new MskConsumer(this, 'MskConsumer', {
      mskClusterArn: props.mskClusterArn,
      mskSecurityGroupId: props.mskSecurityGroupId,
      vpcId: props.vpcId,
      privateSubnetIds: props.privateSubnetIds,
      connectionsTable,
      webSocketApi: webSocketApi.webSocketApi
    });

    // Frontend hosting
    const frontend = new FrontendHosting(this, 'Frontend', {
      userPoolId: cognitoAuth.userPool.userPoolId,
      userPoolClientId: cognitoAuth.userPoolClient.userPoolClientId,
      webSocketUrl: webSocketApi.webSocketUrl,
      region: this.region
    });

    // Outputs
    new cdk.CfnOutput(this, 'UserPoolId', {
      value: cognitoAuth.userPool.userPoolId,
      description: 'Cognito User Pool ID'
    });

    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: cognitoAuth.userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID'
    });

    new cdk.CfnOutput(this, 'WebSocketUrl', {
      value: webSocketApi.webSocketUrl,
      description: 'WebSocket API URL'
    });

    new cdk.CfnOutput(this, 'FrontendUrl', {
      value: frontend.distributionUrl,
      description: 'CloudFront Distribution URL'
    });

    new cdk.CfnOutput(this, 'Region', {
      value: this.region,
      description: 'AWS Region'
    });
  }
}