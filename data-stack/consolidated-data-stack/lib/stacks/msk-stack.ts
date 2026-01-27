import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as msk from 'aws-cdk-lib/aws-msk';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import { Config } from '../config';
import * as path from 'path';

export interface MskStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  mskSecurityGroup: ec2.SecurityGroup;
}

export class MskStack extends cdk.Stack {
  public readonly cluster: msk.CfnCluster;
  public readonly bootstrapServers: string;
  public readonly logGroup: logs.LogGroup;

  constructor(scope: Construct, id: string, props: MskStackProps) {
    super(scope, id, props);

    // S3 bucket for MSK logs
    const logsBucket = new s3.Bucket(this, 'MskLogsBucket', {
      bucketName: `${Config.s3.logsBucketName}-${this.account}-${this.region}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // CloudWatch log group for MSK
    this.logGroup = new logs.LogGroup(this, 'MskLogGroup', {
      logGroupName: `/aws/msk/${Config.msk.clusterName}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Get private subnet IDs
    const privateSubnets = props.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    }).subnetIds;

    // MSK Cluster configuration
    // Shared IAM role for all MSK custom resources to avoid policy race conditions
    const mskCustomResourceRole = new iam.Role(this, 'MskCustomResourceRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    mskCustomResourceRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'kafka:UpdateConnectivity',
        'kafka:DescribeCluster',
        'kafka:DescribeClusterV2',
        'kafka:PutClusterPolicy',
        'kafka:GetClusterPolicy',
        'kafka:CreateConfiguration',
        'kafka:ListConfigurations',
        'kafka:DescribeConfiguration',
        'kafka:UpdateClusterConfiguration',
        'kafka:GetBootstrapBrokers',
      ],
      resources: ['*'],
    }));

    this.cluster = new msk.CfnCluster(this, 'MskCluster', {
      clusterName: Config.msk.clusterName,
      kafkaVersion: Config.msk.kafkaVersion,
      numberOfBrokerNodes: Config.msk.brokerCount,
      brokerNodeGroupInfo: {
        instanceType: Config.msk.brokerInstanceType,
        clientSubnets: privateSubnets,
        securityGroups: [props.mskSecurityGroup.securityGroupId],
        storageInfo: {
          ebsStorageInfo: {
            volumeSize: Config.msk.ebsVolumeSize,
          },
        },
      },
      clientAuthentication: {
        sasl: {
          iam: { enabled: true },
        },
      },
      encryptionInfo: {
        encryptionInTransit: {
          clientBroker: 'TLS',
          inCluster: true,
        },
      },
      enhancedMonitoring: 'PER_TOPIC_PER_BROKER',
      loggingInfo: {
        brokerLogs: {
          cloudWatchLogs: {
            enabled: true,
            logGroup: this.logGroup.logGroupName,
          },
          s3: {
            enabled: true,
            bucket: logsBucket.bucketName,
            prefix: 'msk-logs/',
          },
        },
      },
    });

    // Custom resource to enable Multi-VPC Private Connectivity for Firehose integration
    // This must be done via API call, not CloudFormation property
    const enableVpcConnectivity = new cr.AwsCustomResource(this, 'EnableVpcConnectivity', {
      onCreate: {
        service: 'Kafka',
        action: 'updateConnectivity',
        parameters: {
          ClusterArn: this.cluster.attrArn,
          CurrentVersion: this.cluster.attrCurrentVersion,
          ConnectivityInfo: {
            VpcConnectivity: {
              ClientAuthentication: {
                Sasl: {
                  Iam: { Enabled: true },
                },
              },
            },
          },
        },
        physicalResourceId: cr.PhysicalResourceId.of('EnableVpcConnectivity'),
      },
      role: mskCustomResourceRole,
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({ resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE }),
    });
    enableVpcConnectivity.node.addDependency(this.cluster);

    // Add cluster policy to allow Firehose to create VPC connections
    const clusterPolicy = {
      Version: '2012-10-17',
      Statement: [
        {
          Effect: 'Allow',
          Principal: {
            Service: 'firehose.amazonaws.com',
          },
          Action: [
            'kafka:CreateVpcConnection',
            'kafka:GetBootstrapBrokers',
            'kafka:DescribeCluster',
            'kafka:DescribeClusterV2',
          ],
          Resource: this.cluster.attrArn,
        },
      ],
    };

    const putClusterPolicy = new cr.AwsCustomResource(this, 'PutClusterPolicy', {
      onCreate: {
        service: 'Kafka',
        action: 'putClusterPolicy',
        parameters: {
          ClusterArn: this.cluster.attrArn,
          Policy: JSON.stringify(clusterPolicy),
        },
        physicalResourceId: cr.PhysicalResourceId.of('ClusterPolicy'),
      },
      onUpdate: {
        service: 'Kafka',
        action: 'putClusterPolicy',
        parameters: {
          ClusterArn: this.cluster.attrArn,
          Policy: JSON.stringify(clusterPolicy),
        },
        physicalResourceId: cr.PhysicalResourceId.of('ClusterPolicy'),
      },
      role: mskCustomResourceRole,
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({ resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE }),
    });
    putClusterPolicy.node.addDependency(enableVpcConnectivity);

    // MSK Configuration with auto-topic creation enabled
    // Uses Lambda-backed custom resource for idempotent creation (handles "already exists" case)
    const configName = `${Config.msk.clusterName}-auto-create-topics`;
    const serverProperties = [
      'auto.create.topics.enable=true',
      'default.replication.factor=3',
      'min.insync.replicas=2',
      'num.partitions=3',
    ].join('\n');

    const mskConfigHandler = new lambda.Function(this, 'MskConfigHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/msk-config')),
      timeout: cdk.Duration.minutes(2),
      role: mskCustomResourceRole,
    });

    const mskConfigProvider = new cr.Provider(this, 'MskConfigProvider', {
      onEventHandler: mskConfigHandler,
    });

    const mskConfig = new cdk.CustomResource(this, 'MskConfiguration', {
      serviceToken: mskConfigProvider.serviceToken,
      properties: {
        ConfigurationName: configName,
        KafkaVersions: [Config.msk.kafkaVersion],
        ServerProperties: serverProperties,
      },
    });

    // Get current cluster version for update
    // Note: We need to fetch the current version right before updating
    // since it changes after each cluster operation
    const getClusterVersion = new cr.AwsCustomResource(this, 'GetClusterVersion', {
      onCreate: {
        service: 'Kafka',
        action: 'describeClusterV2',
        parameters: {
          ClusterArn: this.cluster.attrArn,
        },
        physicalResourceId: cr.PhysicalResourceId.of('GetClusterVersion'),
      },
      role: mskCustomResourceRole,
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({ resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE }),
    });
    getClusterVersion.node.addDependency(putClusterPolicy);
    getClusterVersion.node.addDependency(mskConfig);

    // Update cluster to use the MSK configuration
    const updateClusterConfig = new cr.AwsCustomResource(this, 'UpdateClusterConfiguration', {
      onCreate: {
        service: 'Kafka',
        action: 'updateClusterConfiguration',
        parameters: {
          ClusterArn: this.cluster.attrArn,
          CurrentVersion: getClusterVersion.getResponseField('ClusterInfo.CurrentVersion'),
          ConfigurationInfo: {
            Arn: mskConfig.getAttString('Arn'),
            Revision: 1,
          },
        },
        physicalResourceId: cr.PhysicalResourceId.of('UpdateClusterConfiguration'),
      },
      role: mskCustomResourceRole,
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({ resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE }),
    });
    updateClusterConfig.node.addDependency(getClusterVersion);

    // Custom resource to get bootstrap servers
    const getBootstrapServers = new cr.AwsCustomResource(this, 'GetBootstrapServers', {
      onCreate: {
        service: 'Kafka',
        action: 'getBootstrapBrokers',
        parameters: {
          ClusterArn: this.cluster.attrArn,
        },
        physicalResourceId: cr.PhysicalResourceId.of('BootstrapServers'),
      },
      role: mskCustomResourceRole,
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({ resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE }),
    });
    getBootstrapServers.node.addDependency(this.cluster);

    this.bootstrapServers = getBootstrapServers.getResponseField('BootstrapBrokerStringSaslIam');

    // Outputs
    new cdk.CfnOutput(this, 'MskClusterArn', { value: this.cluster.attrArn });
    new cdk.CfnOutput(this, 'BootstrapServers', { value: this.bootstrapServers });
  }
}
