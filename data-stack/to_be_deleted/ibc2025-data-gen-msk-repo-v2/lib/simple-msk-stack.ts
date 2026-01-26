import * as cdk from 'aws-cdk-lib';
import * as msk from 'aws-cdk-lib/aws-msk';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export interface SimpleMskStackProps extends cdk.StackProps {
  vpcId: string;
}

export class SimpleMskStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: SimpleMskStackProps) {
    super(scope, id, props);

    // Import existing VPC
    const vpc = ec2.Vpc.fromLookup(this, 'Vpc', {
      vpcId: props.vpcId,
    });

    // Create security group for MSK
    const securityGroup = new ec2.SecurityGroup(this, 'MskSecurityGroup', {
      vpc,
      description: 'Security group for MSK cluster',
      allowAllOutbound: true,
    });

    // Allow internal traffic
    securityGroup.addIngressRule(
      securityGroup,
      ec2.Port.allTcp(),
      'Allow all TCP traffic within security group'
    );

    // Allow Kafka traffic from VPC
    securityGroup.addIngressRule(
      ec2.Peer.ipv4(vpc.vpcCidrBlock),
      ec2.Port.tcp(9092),
      'Kafka plaintext'
    );
    
    securityGroup.addIngressRule(
      ec2.Peer.ipv4(vpc.vpcCidrBlock),
      ec2.Port.tcp(9094),
      'Kafka TLS'
    );
    
    securityGroup.addIngressRule(
      ec2.Peer.ipv4(vpc.vpcCidrBlock),
      ec2.Port.tcp(9098),
      'Kafka SASL/IAM'
    );

    // Create S3 bucket for MSK logs
    const logBucket = new s3.Bucket(this, 'MskLogBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    // Create CloudWatch log group
    const logGroup = new logs.LogGroup(this, 'MskLogGroup', {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Get private subnets
    const privateSubnets = vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    });

    // Create MSK cluster with IAM auth (without public access initially)
    const cluster = new msk.CfnCluster(this, 'MskCluster', {
      clusterName: `simple-msk-${this.region}`,
      kafkaVersion: '3.5.1',
      numberOfBrokerNodes: 3,
      brokerNodeGroupInfo: {
        instanceType: 'kafka.m5.large',
        clientSubnets: privateSubnets.subnetIds.slice(0, 3),
        securityGroups: [securityGroup.securityGroupId],
        storageInfo: {
          ebsStorageInfo: {
            volumeSize: 100,
          },
        },
        // No public access on creation
        connectivityInfo: {
          publicAccess: {
            type: 'DISABLED',  // Must be DISABLED on creation
          },
        },
      },
      clientAuthentication: {
        sasl: {
          iam: {
            enabled: true,
          },
        },
      },
      encryptionInfo: {
        encryptionInTransit: {
          clientBroker: 'TLS',
          inCluster: true,
        },
      },
      enhancedMonitoring: 'DEFAULT',
      loggingInfo: {
        brokerLogs: {
          cloudWatchLogs: {
            enabled: true,
            logGroup: logGroup.logGroupName,
          },
          s3: {
            enabled: true,
            bucket: logBucket.bucketName,
            prefix: 'msk-logs/',
          },
        },
      },
    });

    // Create S3 buckets for data storage
    const dataBucket = new s3.Bucket(this, 'DataBucket', {
      bucketName: `msk-data-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true,
      lifecycleRules: [
        {
          id: 'transition-old-data',
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30),
            },
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: cdk.Duration.days(90),
            },
          ],
        },
      ],
    });

    // Outputs
    new cdk.CfnOutput(this, 'ClusterArn', {
      value: cluster.attrArn,
      description: 'MSK Cluster ARN',
    });

    new cdk.CfnOutput(this, 'DataBucketName', {
      value: dataBucket.bucketName,
      description: 'S3 bucket for data storage',
    });

    new cdk.CfnOutput(this, 'Instructions', {
      value: `
To complete the setup:
1. Wait for the MSK cluster to become ACTIVE (15-20 minutes)
2. Enable public access: aws kafka update-connectivity --cluster-arn ${cluster.attrArn} --current-version $(aws kafka describe-cluster --cluster-arn ${cluster.attrArn} --query 'ClusterInfo.CurrentVersion' --output text) --connectivity-info '{"PublicAccess":{"Type":"SERVICE_PROVIDED_EIPS"}}' --region ${this.region}
3. Configure producers to write to MSK cluster
      `,
      description: 'Next steps',
    });
  }
}