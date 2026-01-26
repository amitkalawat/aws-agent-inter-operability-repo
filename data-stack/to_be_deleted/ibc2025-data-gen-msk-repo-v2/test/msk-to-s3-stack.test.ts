import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { MskToS3Stack } from '../lib/msk-to-s3-stack';

describe('MskToS3Stack', () => {
  let app: cdk.App;
  let stack: MskToS3Stack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App({
      context: {
        'aws:cdk:enable-lookups': 'false',
      },
    });
    
    stack = new MskToS3Stack(app, 'TestStack', {
      env: {
        account: '123456789012',
        region: 'us-east-1',
      },
      vpcId: 'vpc-12345678',
    });
    
    template = Template.fromStack(stack);
  });

  test('MSK Cluster is created', () => {
    template.hasResourceProperties('AWS::MSK::Cluster', {
      ClusterName: Match.stringLikeRegexp('msk-cluster-'),
      KafkaVersion: Match.anyValue(),
      NumberOfBrokerNodes: 3,
      BrokerNodeGroupInfo: {
        InstanceType: Match.stringLikeRegexp('kafka.m5.'),
        StorageInfo: {
          EBSStorageInfo: {
            VolumeSize: Match.anyValue(),
          },
        },
      },
    });
  });


  test('S3 buckets are created with proper configuration', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      BucketEncryption: {
        ServerSideEncryptionConfiguration: [
          {
            ServerSideEncryptionByDefault: {
              SSEAlgorithm: 'AES256',
            },
          },
        ],
      },
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true,
        BlockPublicPolicy: true,
        IgnorePublicAcls: true,
        RestrictPublicBuckets: true,
      },
      VersioningConfiguration: {
        Status: 'Enabled',
      },
    });
  });


  test('Security group is created for MSK', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: Match.stringLikeRegexp('Security group for MSK cluster'),
      SecurityGroupIngress: Match.arrayWith([
        Match.objectLike({
          IpProtocol: 'tcp',
          FromPort: 9092,
          ToPort: 9092,
        }),
        Match.objectLike({
          IpProtocol: 'tcp',
          FromPort: 9094,
          ToPort: 9094,
        }),
      ]),
    });
  });

  test('CloudWatch dashboard is created', () => {
    template.hasResourceProperties('AWS::CloudWatch::Dashboard', {
      DashboardName: Match.stringLikeRegexp('MSK-S3-Pipeline-'),
    });
  });

  test('CloudWatch alarm is created for high CPU', () => {
    template.hasResourceProperties('AWS::CloudWatch::Alarm', {
      MetricName: 'CpuUtilization',
      Namespace: 'AWS/Kafka',
      Threshold: 80,
      EvaluationPeriods: 2,
      ComparisonOperator: 'GreaterThanThreshold',
    });
  });

  test('Stack outputs are created', () => {
    const outputs = template.findOutputs('*');
    expect(outputs).toHaveProperty('MskClusterArn');
    expect(outputs).toHaveProperty('MskBootstrapServers');
    expect(outputs).toHaveProperty('VpcId');
    expect(outputs).toHaveProperty('Region');
    expect(outputs).toHaveProperty('DashboardUrl');
  });

  test('Log groups are created for monitoring', () => {
    template.hasResourceProperties('AWS::Logs::LogGroup', {
      LogGroupName: Match.stringLikeRegexp('/aws/msk/'),
      RetentionInDays: 7,
    });
  });
});