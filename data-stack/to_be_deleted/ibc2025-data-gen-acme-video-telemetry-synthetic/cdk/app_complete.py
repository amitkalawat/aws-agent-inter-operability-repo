#!/usr/bin/env python3
"""
ACME Telemetry Pipeline CDK Application - Complete Version
Deploys all components based on configuration
"""

import os
import aws_cdk as cdk
from stacks.telemetry_pipeline_stack import TelemetryPipelineStack
from stacks.networking_stack import NetworkingStack
from stacks.msk_stack import MSKStack
from stacks.monitoring_stack import MonitoringStack

# Environment configuration
ACCOUNT = os.environ.get('CDK_DEFAULT_ACCOUNT', '878687028155')
REGION = os.environ.get('CDK_DEFAULT_REGION', 'us-west-2')

app = cdk.App()

# Get configuration from context
vpc_id = app.node.try_get_context("vpc_id")
msk_cluster_arn = app.node.try_get_context("msk_cluster_arn")
s3_bucket_name = app.node.try_get_context("s3_bucket_name")
deploy_networking = app.node.try_get_context("deploy_networking")
deploy_msk = app.node.try_get_context("deploy_msk")
deploy_monitoring = app.node.try_get_context("deploy_monitoring")
alert_email = app.node.try_get_context("alert_email")

# Environment
env = cdk.Environment(account=ACCOUNT, region=REGION)

# Stack dependencies
dependencies = []

# 1. Deploy networking stack if needed
if deploy_networking or not vpc_id:
    print("📡 Deploying Networking Stack...")
    networking_stack = NetworkingStack(
        app, 
        "AcmeTelemetry-Network",
        env=env,
        description="ACME Telemetry Pipeline - VPC and Networking"
    )
    vpc = networking_stack.vpc
    dependencies.append(networking_stack)
else:
    print(f"📡 Using existing VPC: {vpc_id}")
    vpc = None

# 2. Deploy MSK stack if needed
if deploy_msk:
    print("📊 Deploying MSK Stack...")
    if not vpc and not vpc_id:
        raise ValueError("VPC must be provided for MSK deployment")
    
    msk_stack = MSKStack(
        app,
        "AcmeTelemetry-MSK",
        vpc=vpc if vpc else None,
        env=env,
        description="ACME Telemetry Pipeline - MSK Cluster"
    )
    msk_cluster_arn = msk_stack.cluster.attr_arn
    dependencies.append(msk_stack)
    
    if networking_stack:
        msk_stack.add_dependency(networking_stack)
else:
    print(f"📊 Using existing MSK cluster: {msk_cluster_arn[:50]}...")

# 3. Deploy main telemetry pipeline stack
print("🚀 Deploying Telemetry Pipeline Stack...")
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

# Add dependencies
for dep in dependencies:
    telemetry_stack.add_dependency(dep)

# 4. Deploy monitoring stack if needed
if deploy_monitoring:
    print("📈 Deploying Monitoring Stack...")
    monitoring_stack = MonitoringStack(
        app,
        "AcmeTelemetry-Monitoring",
        generator_function=telemetry_stack.generator_function,
        producer_function=telemetry_stack.producer_function,
        alert_email=alert_email,
        env=env,
        description="ACME Telemetry Pipeline - Monitoring and Alarms"
    )
    monitoring_stack.add_dependency(telemetry_stack)

# Add global tags
tags = {
    "Project": "ACME-Telemetry",
    "Environment": "Production",
    "ManagedBy": "CDK",
    "Owner": "DataEngineering",
    "CostCenter": "Engineering",
    "Repository": "ibc2025-data-gen-acme-video-telemetry-synthetic"
}

for key, value in tags.items():
    cdk.Tags.of(app).add(key, value)

# Print deployment summary
print("\n" + "="*60)
print("ACME Telemetry Pipeline CDK Deployment")
print("="*60)
print(f"Account: {ACCOUNT}")
print(f"Region: {REGION}")
print(f"VPC: {'New' if deploy_networking else vpc_id}")
print(f"MSK: {'New' if deploy_msk else 'Existing'}")
print(f"Monitoring: {'Yes' if deploy_monitoring else 'No'}")
if alert_email:
    print(f"Alert Email: {alert_email}")
print("="*60 + "\n")

app.synth()