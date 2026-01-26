#!/usr/bin/env python3
"""
ACME Telemetry Pipeline CDK Application
Main entry point for deploying the complete telemetry infrastructure
"""

import os
import aws_cdk as cdk
from stacks.telemetry_pipeline_stack import TelemetryPipelineStack
from stacks.networking_stack import NetworkingStack

# Environment configuration
ACCOUNT = os.environ.get('CDK_DEFAULT_ACCOUNT', '878687028155')
REGION = os.environ.get('CDK_DEFAULT_REGION', 'us-west-2')

app = cdk.App()

# Get configuration from context
vpc_id = app.node.try_get_context("vpc_id")
msk_cluster_arn = app.node.try_get_context("msk_cluster_arn")
s3_bucket_name = app.node.try_get_context("s3_bucket_name")

# Environment
env = cdk.Environment(account=ACCOUNT, region=REGION)

# Deploy networking stack if VPC ID not provided
networking_stack = None
if not vpc_id:
    networking_stack = NetworkingStack(
        app, 
        "AcmeTelemetry-Network",
        env=env,
        description="ACME Telemetry Pipeline - Networking Infrastructure"
    )
    vpc = networking_stack.vpc
else:
    vpc = None

# Deploy main telemetry pipeline stack
telemetry_stack = TelemetryPipelineStack(
    app,
    "AcmeTelemetry-Pipeline",
    vpc_id=vpc_id,
    vpc=vpc,
    msk_cluster_arn=msk_cluster_arn,
    s3_bucket_name=s3_bucket_name,
    env=env,
    description="ACME Telemetry Pipeline - Lambda, EventBridge, and Firehose"
)

# Add dependencies if networking stack exists
if networking_stack:
    telemetry_stack.add_dependency(networking_stack)

# Add tags
cdk.Tags.of(app).add("Project", "ACME-Telemetry")
cdk.Tags.of(app).add("Environment", "Production")
cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Owner", "DataEngineering")

app.synth()