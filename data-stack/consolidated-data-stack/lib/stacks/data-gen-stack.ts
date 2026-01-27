import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaPython from '@aws-cdk/aws-lambda-python-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as msk from 'aws-cdk-lib/aws-msk';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as firehose from 'aws-cdk-lib/aws-kinesisfirehose';
import { Construct } from 'constructs';
import { Config } from '../config';
import * as path from 'path';

export interface DataGenStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  mskCluster: msk.CfnCluster;
  bootstrapServers: string;
  lambdaSecurityGroup: ec2.SecurityGroup;
  dataBucket: s3.IBucket;
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

    const producerFn = new lambdaPython.PythonFunction(this, 'ProducerFunction', {
      functionName: `${Config.prefix}-producer`,
      runtime: lambda.Runtime.PYTHON_3_11,
      entry: path.join(__dirname, '../../lambda/producer'),
      index: 'handler.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(Config.lambda.timeout),
      memorySize: Config.lambda.producerMemory,
      role: producerRole,
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [props.lambdaSecurityGroup],
      environment: {
        BOOTSTRAP_SERVERS: props.bootstrapServers,
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

    // Firehose IAM role for MSK to S3 delivery
    const firehoseRole = new iam.Role(this, 'FirehoseRole', {
      assumedBy: new iam.ServicePrincipal('firehose.amazonaws.com'),
    });

    // Grant Firehose permissions to read from MSK
    firehoseRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'kafka:DescribeCluster',
        'kafka:DescribeClusterV2',
        'kafka:GetBootstrapBrokers',
        'kafka:CreateVpcConnection',
        'kafka:GetClusterPolicy',
        'kafka-cluster:Connect',
        'kafka-cluster:ReadData',
        'kafka-cluster:DescribeTopic',
        'kafka-cluster:DescribeGroup',
        'kafka-cluster:AlterGroup',
      ],
      resources: ['*'],
    }));

    // Grant Firehose EC2 permissions for VPC connectivity
    firehoseRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'ec2:CreateNetworkInterface',
        'ec2:CreateNetworkInterfacePermission',
        'ec2:DescribeNetworkInterfaces',
        'ec2:DeleteNetworkInterface',
        'ec2:DescribeSecurityGroups',
        'ec2:DescribeSubnets',
        'ec2:DescribeVpcs',
        'ec2:DescribeVpcAttribute',
      ],
      resources: ['*'],
    }));

    // Grant Firehose permissions to write to S3
    props.dataBucket.grantReadWrite(firehoseRole);

    // Firehose delivery stream: MSK -> S3
    const deliveryStream = new firehose.CfnDeliveryStream(this, 'MskToS3DeliveryStream', {
      deliveryStreamName: `${Config.prefix}-msk-to-s3`,
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
        errorOutputPrefix: 'errors/!{firehose:error-output-type}/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/',
        bufferingHints: {
          intervalInSeconds: Config.firehose.bufferInterval,
          sizeInMBs: Config.firehose.bufferSize,
        },
        compressionFormat: 'GZIP',
        cloudWatchLoggingOptions: {
          enabled: true,
          logGroupName: `/aws/firehose/${Config.prefix}-msk-to-s3`,
          logStreamName: 'delivery',
        },
      },
    });

    // Ensure IAM policy is attached before Firehose is created
    deliveryStream.node.addDependency(firehoseRole);

    // Outputs
    new cdk.CfnOutput(this, 'GeneratorFunctionArn', { value: generatorFn.functionArn });
    new cdk.CfnOutput(this, 'ProducerFunctionArn', { value: producerFn.functionArn });
    new cdk.CfnOutput(this, 'FirehoseDeliveryStreamArn', { value: deliveryStream.attrArn });
  }
}
