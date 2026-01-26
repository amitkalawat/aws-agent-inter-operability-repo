import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as firehose from 'aws-cdk-lib/aws-kinesisfirehose';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as msk from 'aws-cdk-lib/aws-msk';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { Config } from '../config';
import * as path from 'path';

export interface DataGenStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  mskCluster: msk.CfnCluster;
  lambdaSecurityGroup: ec2.SecurityGroup;
  dataBucket: s3.Bucket;
}

export class DataGenStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DataGenStackProps) {
    super(scope, id, props);

    // Use Lambda security group from NetworkStack (already has MSK ingress rules configured)

    // Producer Lambda
    const producerRole = new iam.Role(this, 'ProducerRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
      ],
    });

    producerRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'kafka-cluster:Connect',
        'kafka-cluster:WriteData',
        'kafka-cluster:DescribeTopic',
        'kafka-cluster:CreateTopic',
      ],
      resources: ['*'],
    }));

    const producerFn = new lambda.Function(this, 'ProducerFunction', {
      functionName: `${Config.prefix}-producer`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/producer')),
      timeout: cdk.Duration.seconds(Config.lambda.timeout),
      memorySize: Config.lambda.producerMemory,
      role: producerRole,
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [props.lambdaSecurityGroup],
      environment: {
        BOOTSTRAP_SERVERS: cdk.Fn.getAtt(props.mskCluster.logicalId, 'BootstrapBrokers').toString(),
        KAFKA_TOPIC: Config.msk.topics.telemetry,
      },
    });

    // Generator Lambda
    const generatorRole = new iam.Role(this, 'GeneratorRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    generatorRole.addToPolicy(new iam.PolicyStatement({
      actions: ['lambda:InvokeFunction'],
      resources: [producerFn.functionArn],
    }));

    const generatorFn = new lambda.Function(this, 'GeneratorFunction', {
      functionName: `${Config.prefix}-generator`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/generator')),
      timeout: cdk.Duration.seconds(60),
      memorySize: Config.lambda.generatorMemory,
      role: generatorRole,
      environment: {
        BATCH_SIZE: '1000',
        PRODUCER_FUNCTION_NAME: producerFn.functionName,
      },
    });

    // EventBridge rule to trigger generator every 5 minutes
    const rule = new events.Rule(this, 'GeneratorSchedule', {
      ruleName: `${Config.prefix}-generator-schedule`,
      schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
    });
    rule.addTarget(new targets.LambdaFunction(generatorFn));

    // Firehose delivery stream for MSK to S3
    const firehoseRole = new iam.Role(this, 'FirehoseRole', {
      assumedBy: new iam.ServicePrincipal('firehose.amazonaws.com'),
    });

    props.dataBucket.grantReadWrite(firehoseRole);

    firehoseRole.addToPolicy(new iam.PolicyStatement({
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

    const firehoseLogGroup = new logs.LogGroup(this, 'FirehoseLogGroup', {
      logGroupName: `/aws/firehose/${Config.prefix}-delivery`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const deliveryStream = new firehose.CfnDeliveryStream(this, 'DeliveryStream', {
      deliveryStreamName: `${Config.prefix}-delivery-stream`,
      deliveryStreamType: 'MSKAsSource',
      mskSourceConfiguration: {
        mskClusterArn: props.mskCluster.attrArn,
        topicName: Config.msk.topics.telemetry,
        authenticationConfiguration: {
          connectivity: 'PRIVATE',
          roleArn: firehoseRole.roleArn,
        },
      },
      extendedS3DestinationConfiguration: {
        bucketArn: props.dataBucket.bucketArn,
        roleArn: firehoseRole.roleArn,
        prefix: 'telemetry/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/',
        errorOutputPrefix: 'errors/',
        bufferingHints: {
          intervalInSeconds: Config.firehose.bufferInterval,
          sizeInMBs: Config.firehose.bufferSize,
        },
        compressionFormat: 'GZIP',
        cloudWatchLoggingOptions: {
          enabled: true,
          logGroupName: firehoseLogGroup.logGroupName,
          logStreamName: 'delivery',
        },
      },
    });

    // Outputs
    new cdk.CfnOutput(this, 'GeneratorFunctionArn', { value: generatorFn.functionArn });
    new cdk.CfnOutput(this, 'ProducerFunctionArn', { value: producerFn.functionArn });
    new cdk.CfnOutput(this, 'DeliveryStreamName', { value: deliveryStream.deliveryStreamName! });
  }
}
