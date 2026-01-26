import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as msk from 'aws-cdk-lib/aws-msk';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cr from 'aws-cdk-lib/custom-resources';
import { Construct } from 'constructs';
import { Config } from '../config';

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
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({
        resources: [this.cluster.attrArn],
      }),
    });
    getBootstrapServers.node.addDependency(this.cluster);

    this.bootstrapServers = getBootstrapServers.getResponseField('BootstrapBrokerStringSaslIam');

    // Outputs
    new cdk.CfnOutput(this, 'MskClusterArn', { value: this.cluster.attrArn });
    new cdk.CfnOutput(this, 'BootstrapServers', { value: this.bootstrapServers });
  }
}
