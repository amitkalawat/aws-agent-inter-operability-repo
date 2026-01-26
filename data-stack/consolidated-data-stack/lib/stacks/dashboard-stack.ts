import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as apigwv2Integrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as msk from 'aws-cdk-lib/aws-msk';
import { Construct } from 'constructs';
import { Config } from '../config';
import * as path from 'path';

export interface DashboardStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  mskCluster: msk.CfnCluster;
  lambdaSecurityGroup: ec2.SecurityGroup;
}

export class DashboardStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DashboardStackProps) {
    super(scope, id, props);

    // DynamoDB table for WebSocket connections
    const connectionsTable = new dynamodb.Table(this, 'ConnectionsTable', {
      tableName: `${Config.prefix}-connections`,
      partitionKey: { name: 'connectionId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl',
    });

    // Connect handler (AWS SDK v3 is included in Node.js 18.x runtime)
    const connectFn = new lambda.Function(this, 'ConnectFunction', {
      functionName: `${Config.prefix}-ws-connect`,
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'connect.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/websocket')),
      environment: {
        CONNECTIONS_TABLE: connectionsTable.tableName,
      },
    });
    connectionsTable.grantWriteData(connectFn);

    // Disconnect handler
    const disconnectFn = new lambda.Function(this, 'DisconnectFunction', {
      functionName: `${Config.prefix}-ws-disconnect`,
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'disconnect.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/websocket')),
      environment: {
        CONNECTIONS_TABLE: connectionsTable.tableName,
      },
    });
    connectionsTable.grantWriteData(disconnectFn);

    // Default handler
    const defaultFn = new lambda.Function(this, 'DefaultFunction', {
      functionName: `${Config.prefix}-ws-default`,
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'default.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/websocket')),
    });

    // WebSocket API
    const webSocketApi = new apigwv2.WebSocketApi(this, 'WebSocketApi', {
      apiName: `${Config.prefix}-websocket`,
      connectRouteOptions: {
        integration: new apigwv2Integrations.WebSocketLambdaIntegration('ConnectIntegration', connectFn),
      },
      disconnectRouteOptions: {
        integration: new apigwv2Integrations.WebSocketLambdaIntegration('DisconnectIntegration', disconnectFn),
      },
      defaultRouteOptions: {
        integration: new apigwv2Integrations.WebSocketLambdaIntegration('DefaultIntegration', defaultFn),
      },
    });

    const stage = new apigwv2.WebSocketStage(this, 'WebSocketStage', {
      webSocketApi,
      stageName: 'prod',
      autoDeploy: true,
    });

    // MSK Consumer Lambda (uses Lambda security group from NetworkStack)
    const consumerRole = new iam.Role(this, 'ConsumerRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
      ],
    });

    consumerRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'kafka:DescribeCluster',
        'kafka:GetBootstrapBrokers',
        'kafka-cluster:Connect',
        'kafka-cluster:ReadData',
        'kafka-cluster:DescribeTopic',
        'kafka-cluster:DescribeGroup',
      ],
      resources: ['*'],
    }));

    // Grant WebSocket management permissions
    consumerRole.addToPolicy(new iam.PolicyStatement({
      actions: ['execute-api:ManageConnections'],
      resources: [`arn:aws:execute-api:${this.region}:${this.account}:${webSocketApi.apiId}/*`],
    }));

    const consumerFn = new lambda.Function(this, 'ConsumerFunction', {
      functionName: `${Config.prefix}-msk-consumer`,
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/consumer')),
      role: consumerRole,
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [props.lambdaSecurityGroup],
      timeout: cdk.Duration.minutes(5),
      memorySize: Config.lambda.consumerMemory,
      environment: {
        CONNECTIONS_TABLE: connectionsTable.tableName,
        WEBSOCKET_ENDPOINT: stage.callbackUrl,
      },
    });
    connectionsTable.grantReadWriteData(consumerFn);

    // MSK event source (requires cluster to be available)
    consumerFn.addEventSource(new lambdaEventSources.ManagedKafkaEventSource({
      clusterArn: props.mskCluster.attrArn,
      topic: Config.msk.topics.telemetry,
      batchSize: 100,
      startingPosition: lambda.StartingPosition.LATEST,
    }));

    // Outputs
    new cdk.CfnOutput(this, 'WebSocketApiEndpoint', { value: stage.url });
    new cdk.CfnOutput(this, 'ConnectionsTableName', { value: connectionsTable.tableName });
  }
}
