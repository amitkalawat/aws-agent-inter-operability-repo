import * as cdk from 'aws-cdk-lib';
import * as msk from 'aws-cdk-lib/aws-msk';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export interface MskClusterProps {
  vpc: ec2.IVpc;
  clusterName?: string;
  kafkaVersion?: string;
  instanceType?: ec2.InstanceType;
  numberOfBrokerNodes?: number;
  ebsVolumeSize?: number;
  logGroup?: logs.ILogGroup;
  logBucket?: s3.IBucket;
}

export class MskCluster extends Construct {
  public readonly cluster: msk.CfnCluster;
  public readonly securityGroup: ec2.SecurityGroup;
  public readonly bootstrapServers: string;
  public readonly clusterArn: string;
  public readonly clusterName: string;

  constructor(scope: Construct, id: string, props: MskClusterProps) {
    super(scope, id);

    const clusterName = props.clusterName || `msk-cluster-${cdk.Stack.of(this).stackName}`;
    
    this.securityGroup = new ec2.SecurityGroup(this, 'MskSecurityGroup', {
      vpc: props.vpc,
      description: 'Security group for MSK cluster',
      allowAllOutbound: true,
    });

    this.securityGroup.addIngressRule(
      this.securityGroup,
      ec2.Port.allTcp(),
      'Allow all TCP traffic within the security group'
    );

    this.securityGroup.addIngressRule(
      ec2.Peer.ipv4(props.vpc.vpcCidrBlock),
      ec2.Port.tcp(9098),
      'Allow Kafka SASL/IAM traffic from VPC'
    );

    this.securityGroup.addIngressRule(
      ec2.Peer.ipv4(props.vpc.vpcCidrBlock),
      ec2.Port.tcp(9094),
      'Allow Kafka TLS traffic from VPC'
    );

    this.securityGroup.addIngressRule(
      ec2.Peer.ipv4(props.vpc.vpcCidrBlock),
      ec2.Port.tcp(2181),
      'Allow ZooKeeper traffic from VPC'
    );

    const logGroup = props.logGroup || new logs.LogGroup(this, 'MskLogGroup', {
      logGroupName: `/aws/msk/${clusterName}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const logBucket = props.logBucket || new s3.Bucket(this, 'MskLogBucket', {
      bucketName: `${clusterName}-logs-${cdk.Stack.of(this).account}-${cdk.Stack.of(this).region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          id: 'delete-old-logs',
          expiration: cdk.Duration.days(30),
        },
      ],
    });

    const privateSubnets = props.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    });

    const numberOfBrokerNodes = props.numberOfBrokerNodes || 3;
    const selectedSubnets = privateSubnets.subnets.slice(0, numberOfBrokerNodes);

    this.cluster = new msk.CfnCluster(this, 'Cluster', {
      clusterName: clusterName,
      kafkaVersion: props.kafkaVersion || '3.5.1',
      numberOfBrokerNodes: numberOfBrokerNodes,
      brokerNodeGroupInfo: {
        instanceType: props.instanceType?.toString() || 'kafka.m5.large',
        clientSubnets: selectedSubnets.map(s => s.subnetId),
        securityGroups: [this.securityGroup.securityGroupId],
        storageInfo: {
          ebsStorageInfo: {
            volumeSize: props.ebsVolumeSize || 100,
          },
        },
        connectivityInfo: {
          publicAccess: {
            type: 'SERVICE_PROVIDED_EIPS',
          },
        },
      },
      loggingInfo: {
        brokerLogs: {
          cloudWatchLogs: {
            enabled: true,
            logGroup: logGroup.logGroupName,
          },
          s3: {
            enabled: true,
            bucket: logBucket.bucketName,
            prefix: 'broker-logs',
          },
        },
      },
      enhancedMonitoring: 'PER_TOPIC_PER_BROKER',
      encryptionInfo: {
        encryptionInTransit: {
          clientBroker: 'TLS',
          inCluster: true,
        },
      },
      clientAuthentication: {
        sasl: {
          iam: {
            enabled: true,
          },
        },
      },
    });

    this.clusterArn = this.cluster.attrArn;
    this.clusterName = clusterName;

    // Create custom resource to get bootstrap brokers
    const getBootstrapBrokers = new cdk.custom_resources.AwsCustomResource(this, 'GetBootstrapBrokers', {
      onUpdate: {
        service: 'Kafka',
        action: 'getBootstrapBrokers',
        parameters: {
          ClusterArn: this.cluster.attrArn,
        },
        physicalResourceId: cdk.custom_resources.PhysicalResourceId.of(this.cluster.attrArn),
      },
      policy: cdk.custom_resources.AwsCustomResourcePolicy.fromStatements([
        new iam.PolicyStatement({
          actions: ['kafka:GetBootstrapBrokers'],
          resources: [this.cluster.attrArn],
        }),
      ]),
    });

    getBootstrapBrokers.node.addDependency(this.cluster);
    
    this.bootstrapServers = getBootstrapBrokers.getResponseField('BootstrapBrokerStringSaslIam');

    new cdk.CfnOutput(this, 'MskClusterArn', {
      value: this.clusterArn,
      description: 'ARN of the MSK cluster',
      exportName: `${cdk.Stack.of(this).stackName}-MskClusterArn`,
    });

    new cdk.CfnOutput(this, 'MskBootstrapServers', {
      value: this.bootstrapServers,
      description: 'Bootstrap servers for the MSK cluster',
      exportName: `${cdk.Stack.of(this).stackName}-MskBootstrapServers`,
    });

    new cdk.CfnOutput(this, 'MskSecurityGroupId', {
      value: this.securityGroup.securityGroupId,
      description: 'Security group ID for the MSK cluster',
      exportName: `${cdk.Stack.of(this).stackName}-MskSecurityGroupId`,
    });
  }
}