"""
ACME Telemetry Pipeline Stack
Main CDK stack containing Lambda functions, EventBridge rules, and Firehose delivery stream
"""

import os
from pathlib import Path
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_kinesisfirehose as firehose,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_logs as logs,
    CfnOutput
)
from constructs import Construct

class TelemetryPipelineStack(Stack):
    """Main stack for ACME telemetry pipeline"""
    
    def __init__(self, scope: Construct, construct_id: str, 
                 vpc_id: str = None, vpc: ec2.IVpc = None,
                 msk_cluster_arn: str = None, 
                 s3_bucket_name: str = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Get or create VPC
        if vpc:
            self.vpc = vpc
        elif vpc_id:
            self.vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id)
        else:
            raise ValueError("Either vpc or vpc_id must be provided")
        
        # MSK Configuration
        if not msk_cluster_arn:
            msk_cluster_arn = self.node.try_get_context("msk_cluster_arn")
            if not msk_cluster_arn:
                raise ValueError("MSK cluster ARN must be provided")
        
        self.msk_cluster_arn = msk_cluster_arn
        
        # S3 Bucket for data storage
        if s3_bucket_name:
            self.data_bucket = s3.Bucket.from_bucket_name(
                self, "DataBucket", s3_bucket_name
            )
        else:
            self.data_bucket = s3.Bucket(
                self, "TelemetryDataBucket",
                bucket_name=f"acme-telemetry-{self.account}-{self.region}",
                encryption=s3.BucketEncryption.S3_MANAGED,
                lifecycle_rules=[
                    s3.LifecycleRule(
                        id="DeleteOldData",
                        expiration=Duration.days(90),
                        transitions=[
                            s3.Transition(
                                storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                                transition_after=Duration.days(30)
                            ),
                            s3.Transition(
                                storage_class=s3.StorageClass.GLACIER,
                                transition_after=Duration.days(60)
                            )
                        ]
                    )
                ],
                removal_policy=RemovalPolicy.RETAIN
            )
        
        # Security Group for Lambda functions
        self.lambda_sg = ec2.SecurityGroup(
            self, "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda functions accessing MSK",
            allow_all_outbound=True
        )
        
        # Add rule for MSK access
        self.lambda_sg.add_ingress_rule(
            peer=self.lambda_sg,
            connection=ec2.Port.tcp(9098),
            description="MSK IAM auth"
        )
        
        # Create Lambda Layer for dependencies
        self.dependencies_layer = self.create_dependencies_layer()
        
        # Create IAM roles
        self.generator_role = self.create_generator_role()
        self.producer_role = self.create_producer_role()
        self.firehose_role = self.create_firehose_role()
        
        # Create Lambda functions
        self.producer_function = self.create_producer_lambda()
        self.generator_function = self.create_generator_lambda()
        
        # Create EventBridge rule
        self.create_eventbridge_rule()
        
        # Create MSK cluster resource policy
        self.update_msk_cluster_policy()
        
        # Create Kinesis Data Firehose
        self.create_firehose_delivery_stream()
        
        # Outputs
        self.create_outputs()
    
    def create_dependencies_layer(self) -> lambda_.LayerVersion:
        """Create Lambda layer with Python dependencies"""
        return lambda_.LayerVersion(
            self, "DependenciesLayer",
            code=lambda_.Code.from_asset(
                "../lambda/msk_producer",
                bundling={
                    "image": lambda_.Runtime.PYTHON_3_9.bundling_image,
                    "command": [
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output/python && " +
                        "cp -r . /asset-output/python/"
                    ]
                }
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
            description="Dependencies for MSK producer Lambda"
        )
    
    def create_generator_role(self) -> iam.Role:
        """Create IAM role for Generator Lambda"""
        role = iam.Role(
            self, "GeneratorRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={
                "GeneratorPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["lambda:InvokeFunction"],
                            resources=["*"]  # Will be restricted to producer ARN later
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "cloudwatch:PutMetricData"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        return role
    
    def create_producer_role(self) -> iam.Role:
        """Create IAM role for Producer Lambda"""
        role = iam.Role(
            self, "ProducerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            ],
            inline_policies={
                "ProducerPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "kafka:GetBootstrapBrokers",
                                "kafka:DescribeCluster",
                                "kafka:DescribeClusterV2",
                                "kafka-cluster:Connect",
                                "kafka-cluster:AlterCluster",
                                "kafka-cluster:DescribeCluster",
                                "kafka-cluster:WriteData",
                                "kafka-cluster:DescribeTopic",
                                "kafka-cluster:AlterTopic",
                                "kafka-cluster:CreateTopic",
                                "kafka-cluster:ReadData",
                                "kafka-cluster:AlterGroup",
                                "kafka-cluster:DescribeGroup"
                            ],
                            resources=[
                                self.msk_cluster_arn,
                                f"{self.msk_cluster_arn}/*"
                            ]
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "cloudwatch:PutMetricData"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        return role
    
    def create_firehose_role(self) -> iam.Role:
        """Create IAM role for Kinesis Firehose"""
        role = iam.Role(
            self, "FirehoseRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
            inline_policies={
                "FirehosePolicy": iam.PolicyDocument(
                    statements=[
                        # S3 permissions
                        iam.PolicyStatement(
                            actions=[
                                "s3:AbortMultipartUpload",
                                "s3:GetBucketLocation",
                                "s3:GetObject",
                                "s3:ListBucket",
                                "s3:ListBucketMultipartUploads",
                                "s3:PutObject"
                            ],
                            resources=[
                                self.data_bucket.bucket_arn,
                                f"{self.data_bucket.bucket_arn}/*"
                            ]
                        ),
                        # MSK permissions
                        iam.PolicyStatement(
                            actions=[
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
                            resources=[
                                self.msk_cluster_arn,
                                f"{self.msk_cluster_arn}/*"
                            ]
                        ),
                        # VPC permissions for MSK
                        iam.PolicyStatement(
                            actions=[
                                "ec2:DescribeVpcs",
                                "ec2:DescribeVpcAttribute",
                                "ec2:DescribeSubnets",
                                "ec2:DescribeSecurityGroups",
                                "ec2:DescribeNetworkInterfaces",
                                "ec2:CreateNetworkInterface",
                                "ec2:CreateNetworkInterfacePermission",
                                "ec2:DeleteNetworkInterface"
                            ],
                            resources=["*"]
                        ),
                        # CloudWatch logs
                        iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        return role
    
    def create_producer_lambda(self) -> lambda_.Function:
        """Create MSK Producer Lambda function"""
        function = lambda_.Function(
            self, "ProducerFunction",
            function_name="AcmeTelemetry-Producer",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/msk_producer"),
            layers=[self.dependencies_layer],
            role=self.producer_role,
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_groups=[self.lambda_sg],
            environment={
                "MSK_CLUSTER_ARN": self.msk_cluster_arn,
                "TOPIC_NAME": "acme-telemetry",
                "AWS_DEFAULT_REGION": self.region
            },
            timeout=Duration.seconds(60),
            memory_size=512,
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        return function
    
    def create_generator_lambda(self) -> lambda_.Function:
        """Create Telemetry Generator Lambda function"""
        function = lambda_.Function(
            self, "GeneratorFunction",
            function_name="AcmeTelemetry-Generator",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/telemetry_generator"),
            role=self.generator_role,
            environment={
                "MSK_PRODUCER_FUNCTION_NAME": self.producer_function.function_name
            },
            timeout=Duration.seconds(300),
            memory_size=1024,
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Grant invoke permission to generator for producer
        self.producer_function.grant_invoke(function)
        
        return function
    
    def create_eventbridge_rule(self) -> events.Rule:
        """Create EventBridge scheduled rule"""
        rule = events.Rule(
            self, "GeneratorSchedule",
            rule_name="AcmeTelemetry-GeneratorSchedule",
            description="Trigger telemetry generation every 5 minutes",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            enabled=True
        )
        
        # Add Lambda target
        rule.add_target(
            targets.LambdaFunction(
                self.generator_function,
                retry_attempts=2
            )
        )
        
        return rule
    
    def update_msk_cluster_policy(self):
        """Update MSK cluster resource policy for Firehose access"""
        # Note: This would typically be done via Custom Resource
        # For now, we'll document this as a manual step
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "firehose.amazonaws.com"
                    },
                    "Action": [
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
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceAccount": self.account
                        }
                    }
                }
            ]
        }
        
        # Output the policy for manual application
        CfnOutput(
            self, "MSKClusterPolicy",
            value=str(policy_document),
            description="Apply this policy to your MSK cluster using AWS CLI"
        )
    
    def create_firehose_delivery_stream(self):
        """Create Kinesis Data Firehose delivery stream"""
        
        # Log group for Firehose
        log_group = logs.LogGroup(
            self, "FirehoseLogGroup",
            log_group_name="/aws/kinesisfirehose/AcmeTelemetry-MSK-to-S3",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create Firehose delivery stream
        delivery_stream = firehose.CfnDeliveryStream(
            self, "TelemetryFirehose",
            delivery_stream_name="AcmeTelemetry-MSK-to-S3",
            delivery_stream_type="MSKAsSource",
            msk_source_configuration=firehose.CfnDeliveryStream.MSKSourceConfigurationProperty(
                msk_cluster_arn=self.msk_cluster_arn,
                topic_name="acme-telemetry",
                authentication_configuration=firehose.CfnDeliveryStream.AuthenticationConfigurationProperty(
                    role_arn=self.firehose_role.role_arn,
                    connectivity="PRIVATE"
                )
            ),
            extended_s3_destination_configuration=firehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=self.data_bucket.bucket_arn,
                prefix="telemetry/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/",
                error_output_prefix="errors/!{firehose:error-output-type}/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
                buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                    size_in_m_bs=128,
                    interval_in_seconds=300
                ),
                compression_format="GZIP",
                role_arn=self.firehose_role.role_arn,
                cloud_watch_logging_options=firehose.CfnDeliveryStream.CloudWatchLoggingOptionsProperty(
                    enabled=True,
                    log_group_name=log_group.log_group_name,
                    log_stream_name="S3Delivery"
                )
            )
        )
        
        # Ensure log group is created before Firehose
        delivery_stream.node.add_dependency(log_group)
        
        return delivery_stream
    
    def create_outputs(self):
        """Create stack outputs"""
        CfnOutput(
            self, "GeneratorFunctionArn",
            value=self.generator_function.function_arn,
            description="ARN of the Telemetry Generator Lambda function"
        )
        
        CfnOutput(
            self, "ProducerFunctionArn",
            value=self.producer_function.function_arn,
            description="ARN of the MSK Producer Lambda function"
        )
        
        CfnOutput(
            self, "DataBucketName",
            value=self.data_bucket.bucket_name,
            description="Name of the S3 bucket for telemetry data"
        )
        
        CfnOutput(
            self, "SecurityGroupId",
            value=self.lambda_sg.security_group_id,
            description="Security group ID for Lambda functions"
        )
        
        CfnOutput(
            self, "MSKClusterArn",
            value=self.msk_cluster_arn,
            description="ARN of the MSK cluster"
        )