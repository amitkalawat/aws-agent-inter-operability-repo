import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { Config } from '../config';

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.IVpc;
  public readonly mskSecurityGroup: ec2.SecurityGroup;
  public readonly lambdaSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create VPC with public and private subnets
    this.vpc = new ec2.Vpc(this, 'AcmeVpc', {
      vpcName: `${Config.prefix}-vpc`,
      maxAzs: 3,
      natGateways: 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
    });

    // Security group for MSK cluster
    this.mskSecurityGroup = new ec2.SecurityGroup(this, 'MskSecurityGroup', {
      vpc: this.vpc,
      securityGroupName: `${Config.prefix}-msk-sg`,
      description: 'Security group for MSK cluster',
      allowAllOutbound: true,
    });

    // Security group for Lambda functions
    this.lambdaSecurityGroup = new ec2.SecurityGroup(this, 'LambdaSecurityGroup', {
      vpc: this.vpc,
      securityGroupName: `${Config.prefix}-lambda-sg`,
      description: 'Security group for Lambda functions',
      allowAllOutbound: true,
    });

    // Allow Lambda to connect to MSK (SASL/IAM port)
    this.mskSecurityGroup.addIngressRule(
      this.lambdaSecurityGroup,
      ec2.Port.tcp(9098),
      'Allow Lambda SASL/IAM access to MSK'
    );

    // Allow MSK internal communication
    this.mskSecurityGroup.addIngressRule(
      this.mskSecurityGroup,
      ec2.Port.allTraffic(),
      'Allow MSK internal communication'
    );

    // Outputs
    new cdk.CfnOutput(this, 'VpcId', { value: this.vpc.vpcId });
    new cdk.CfnOutput(this, 'MskSecurityGroupId', { value: this.mskSecurityGroup.securityGroupId });
  }
}
