import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import { Construct } from 'constructs';
import { MskCluster } from './constructs/msk-cluster';

export interface MskToS3StackProps extends cdk.StackProps {
  vpcId: string;
  mskInstanceType?: ec2.InstanceType;
  numberOfBrokerNodes?: number;
  ebsVolumeSize?: number;
}

export class MskToS3Stack extends cdk.Stack {
  public readonly mskCluster: MskCluster;
  public readonly vpc: ec2.IVpc;

  constructor(scope: Construct, id: string, props: MskToS3StackProps) {
    super(scope, id, props);

    this.vpc = ec2.Vpc.fromLookup(this, 'Vpc', {
      vpcId: props.vpcId,
    });

    this.mskCluster = new MskCluster(this, 'MskCluster', {
      vpc: this.vpc,
      clusterName: `msk-cluster-${this.region}`,
      instanceType: props.mskInstanceType || ec2.InstanceType.of(
        ec2.InstanceClass.M5,
        ec2.InstanceSize.LARGE
      ),
      numberOfBrokerNodes: props.numberOfBrokerNodes || 3,
      ebsVolumeSize: props.ebsVolumeSize || 100,
      kafkaVersion: '3.5.1',
    });

    this.createDashboard();

    this.createOutputs();
  }

  private createDashboard() {
    const dashboard = new cloudwatch.Dashboard(this, 'MskS3Dashboard', {
      dashboardName: `MSK-S3-Pipeline-${this.region}`,
    });

    const bytesInPerSec = new cloudwatch.Metric({
      namespace: 'AWS/Kafka',
      metricName: 'BytesInPerSec',
      dimensionsMap: {
        'Cluster Name': this.mskCluster.clusterName,
      },
      statistic: 'Average',
      period: cdk.Duration.minutes(5),
    });

    const bytesOutPerSec = new cloudwatch.Metric({
      namespace: 'AWS/Kafka',
      metricName: 'BytesOutPerSec',
      dimensionsMap: {
        'Cluster Name': this.mskCluster.clusterName,
      },
      statistic: 'Average',
      period: cdk.Duration.minutes(5),
    });

    const cpuUtilization = new cloudwatch.Metric({
      namespace: 'AWS/Kafka',
      metricName: 'CpuUtilization',
      dimensionsMap: {
        'Cluster Name': this.mskCluster.clusterName,
      },
      statistic: 'Average',
      period: cdk.Duration.minutes(5),
    });

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'MSK Cluster Throughput',
        left: [bytesInPerSec],
        right: [bytesOutPerSec],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: 'MSK Cluster CPU Utilization',
        left: [cpuUtilization],
        width: 12,
        height: 6,
      })
    );

    const alarmWidget = new cloudwatch.AlarmWidget({
      title: 'Pipeline Alarms',
      alarm: new cloudwatch.Alarm(this, 'HighCpuAlarm', {
        metric: cpuUtilization,
        threshold: 80,
        evaluationPeriods: 2,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        alarmDescription: 'MSK Cluster CPU utilization is too high',
      }),
      width: 24,
      height: 4,
    });

    dashboard.addWidgets(alarmWidget);
  }

  private createOutputs() {
    new cdk.CfnOutput(this, 'VpcId', {
      value: this.vpc.vpcId,
      description: 'VPC ID used for the MSK cluster',
    });

    new cdk.CfnOutput(this, 'Region', {
      value: this.region,
      description: 'AWS Region where the stack is deployed',
    });

    new cdk.CfnOutput(this, 'DashboardUrl', {
      value: `https://${this.region}.console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=MSK-S3-Pipeline-${this.region}`,
      description: 'URL to the CloudWatch Dashboard',
    });

    new cdk.CfnOutput(this, 'StackArn', {
      value: this.stackId,
      description: 'ARN of this CloudFormation stack',
    });
  }
}