"""
ACME Telemetry Pipeline - MSK Stack
Optional stack for creating Amazon MSK cluster if not using existing cluster
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_msk as msk,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput
)
from constructs import Construct

class MSKStack(Stack):
    """Optional MSK cluster stack for ACME telemetry pipeline"""
    
    def __init__(self, scope: Construct, construct_id: str, 
                 vpc: ec2.IVpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.vpc = vpc
        
        # Security group for MSK cluster
        self.msk_security_group = ec2.SecurityGroup(
            self, "MSKSecurityGroup",
            vpc=self.vpc,
            description="Security group for MSK cluster",
            allow_all_outbound=True
        )
        
        # Allow internal communication
        self.msk_security_group.add_ingress_rule(
            peer=self.msk_security_group,
            connection=ec2.Port.all_tcp(),
            description="Allow MSK internal communication"
        )
        
        # Allow Lambda access on IAM auth port
        self.msk_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(9098),
            description="MSK IAM authentication"
        )
        
        # Allow plaintext for internal communication (optional)
        self.msk_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(9092),
            description="MSK plaintext"
        )
        
        # CloudWatch log group for MSK
        self.log_group = logs.LogGroup(
            self, "MSKLogGroup",
            log_group_name="/aws/msk/acme-telemetry-cluster",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # MSK Configuration
        msk_config = msk.CfnConfiguration(
            self, "MSKConfiguration",
            name="acme-telemetry-config",
            kafka_versions_list=["2.8.1"],
            server_properties="""
auto.create.topics.enable=true
default.replication.factor=3
min.insync.replicas=2
num.partitions=20
log.retention.hours=168
compression.type=gzip
"""
        )
        
        # Create MSK Cluster
        self.cluster = msk.CfnCluster(
            self, "MSKCluster",
            cluster_name="acme-telemetry-msk",
            kafka_version="2.8.1",
            number_of_broker_nodes=3,
            broker_node_group_info=msk.CfnCluster.BrokerNodeGroupInfoProperty(
                instance_type="kafka.m5.large",
                client_subnets=[subnet.subnet_id for subnet in self.vpc.private_subnets[:3]],
                security_groups=[self.msk_security_group.security_group_id],
                storage_info=msk.CfnCluster.StorageInfoProperty(
                    ebs_storage_info=msk.CfnCluster.EBSStorageInfoProperty(
                        volume_size=100,
                        provisioned_throughput=msk.CfnCluster.ProvisionedThroughputProperty(
                            enabled=False
                        )
                    )
                ),
                connectivity_info=msk.CfnCluster.ConnectivityInfoProperty(
                    public_access=msk.CfnCluster.PublicAccessProperty(
                        type="DISABLED"
                    ),
                    vpc_connectivity=msk.CfnCluster.VpcConnectivityProperty(
                        client_authentication=msk.CfnCluster.VpcConnectivityClientAuthenticationProperty(
                            sasl=msk.CfnCluster.VpcConnectivitySaslProperty(
                                iam=msk.CfnCluster.VpcConnectivityIamProperty(
                                    enabled=True
                                )
                            )
                        )
                    )
                )
            ),
            client_authentication=msk.CfnCluster.ClientAuthenticationProperty(
                sasl=msk.CfnCluster.SaslProperty(
                    iam=msk.CfnCluster.IamProperty(
                        enabled=True
                    )
                )
            ),
            configuration_info=msk.CfnCluster.ConfigurationInfoProperty(
                arn=msk_config.ref,
                revision=1
            ),
            encryption_info=msk.CfnCluster.EncryptionInfoProperty(
                encryption_in_transit=msk.CfnCluster.EncryptionInTransitProperty(
                    client_broker="TLS",
                    in_cluster=True
                )
            ),
            enhanced_monitoring="PER_TOPIC_PER_BROKER",
            logging_info=msk.CfnCluster.LoggingInfoProperty(
                broker_logs=msk.CfnCluster.BrokerLogsProperty(
                    cloud_watch_logs=msk.CfnCluster.CloudWatchLogsProperty(
                        enabled=True,
                        log_group=self.log_group.log_group_name
                    )
                )
            ),
            tags={
                "Name": "acme-telemetry-msk",
                "Project": "ACME-Telemetry",
                "Environment": "Production"
            }
        )
        
        # Ensure log group is created before cluster
        self.cluster.node.add_dependency(self.log_group)
        
        # Create cluster policy for Firehose access
        cluster_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("firehose.amazonaws.com")],
                    actions=[
                        "kafka:CreateVpcConnection",
                        "kafka:GetBootstrapBrokers",
                        "kafka:DescribeCluster",
                        "kafka:DescribeClusterV2",
                        "kafka-cluster:Connect",
                        "kafka-cluster:DescribeCluster",
                        "kafka-cluster:ReadData",
                        "kafka-cluster:DescribeGroup",
                        "kafka-cluster:AlterGroup",
                        "kafka-cluster:DescribeTopic"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "aws:SourceAccount": self.account
                        }
                    }
                )
            ]
        )
        
        # Note: Cluster policy would need to be applied via Custom Resource or CLI
        CfnOutput(
            self, "ClusterPolicyCommand",
            value=f"aws kafka put-cluster-policy --cluster-arn {self.cluster.attr_arn} --policy '{cluster_policy.to_json()}'",
            description="Run this command to apply the cluster policy"
        )
        
        # Outputs
        CfnOutput(
            self, "MSKClusterArn",
            value=self.cluster.attr_arn,
            description="ARN of the MSK cluster",
            export_name="MSKClusterArn"
        )
        
        CfnOutput(
            self, "MSKSecurityGroupId",
            value=self.msk_security_group.security_group_id,
            description="Security group ID for MSK cluster"
        )