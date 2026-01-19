import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as eventsources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as cdk from 'aws-cdk-lib';
import * as path from 'path';

export interface MskConsumerProps {
  mskClusterArn: string;
  mskSecurityGroupId: string;
  vpcId: string;
  privateSubnetIds: string[];
  connectionsTable: dynamodb.Table;
  webSocketApi: apigatewayv2.WebSocketApi;
}

export class MskConsumer extends Construct {
  public readonly consumerFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: MskConsumerProps) {
    super(scope, id);

    // Import VPC
    const vpc = ec2.Vpc.fromLookup(this, 'Vpc', { vpcId: props.vpcId });
    
    // Import security group
    const securityGroup = ec2.SecurityGroup.fromSecurityGroupId(
      this, 'SecurityGroup', props.mskSecurityGroupId
    );

    // MSK Consumer Lambda
    this.consumerFunction = new lambda.Function(this, 'ConsumerFunction', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'consumer.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../backend/lambdas/msk')),
      vpc,
      vpcSubnets: {
        subnets: props.privateSubnetIds.map((id, index) => 
          ec2.Subnet.fromSubnetId(this, `Subnet${index}`, id)
        )
      },
      securityGroups: [securityGroup],
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        CONNECTIONS_TABLE: props.connectionsTable.tableName,
        WEBSOCKET_ENDPOINT: `https://${props.webSocketApi.apiId}.execute-api.${cdk.Stack.of(this).region}.amazonaws.com/prod`
      }
    });

    // Grant permissions
    props.connectionsTable.grantReadWriteData(this.consumerFunction);
    
    // Grant API Gateway management permissions
    this.consumerFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['execute-api:ManageConnections'],
      resources: [`arn:aws:execute-api:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:${props.webSocketApi.apiId}/*`]
    }));

    // MSK permissions for IAM authentication
    this.consumerFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'kafka:DescribeCluster',
        'kafka:DescribeClusterV2',
        'kafka:GetBootstrapBrokers',
        'kafka-cluster:Connect',
        'kafka-cluster:DescribeGroup',
        'kafka-cluster:AlterGroup',
        'kafka-cluster:DescribeTopic',
        'kafka-cluster:ReadData',
        'kafka-cluster:DescribeClusterDynamicConfiguration'
      ],
      resources: [
        props.mskClusterArn,
        `${props.mskClusterArn}/*`
      ]
    }));

    // Add MSK event source with IAM authentication
    const eventSource = new eventsources.ManagedKafkaEventSource({
      clusterArn: props.mskClusterArn,
      topic: 'acme-telemetry',
      startingPosition: lambda.StartingPosition.LATEST,
      batchSize: 100,
      maxBatchingWindow: cdk.Duration.seconds(5)
    });

    this.consumerFunction.addEventSource(eventSource);
  }
}