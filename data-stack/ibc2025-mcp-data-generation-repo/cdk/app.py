#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.data_lake_stack import DataLakeStack
from stacks.glue_stack import GlueStack
# from stacks.analytics_stack import AnalyticsStack  # Commented for testing

app = cdk.App()

# Get configuration from context
env_config = {
    'account': app.node.try_get_context('account') or os.environ.get('CDK_DEFAULT_ACCOUNT'),
    'region': app.node.try_get_context('region') or os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')
}

# Stack naming prefix
stack_prefix = "AcmeStreamingData"

# Create the data lake stack (S3 bucket and basic infrastructure)
data_lake_stack = DataLakeStack(
    app, 
    f"{stack_prefix}-DataLake",
    env=env_config,
    description="S3 data lake for Acme Corp streaming platform data"
)

# Create the Glue stack (database, tables, crawlers)
glue_stack = GlueStack(
    app,
    f"{stack_prefix}-Glue",
    data_bucket=data_lake_stack.data_bucket,
    env=env_config,
    description="AWS Glue catalog for Acme Corp streaming data"
)
glue_stack.add_dependency(data_lake_stack)

# Create the analytics stack (Athena, Redshift)
# Commenting out for testing - Redshift requires additional setup
# analytics_stack = AnalyticsStack(
#     app,
#     f"{stack_prefix}-Analytics",
#     data_bucket=data_lake_stack.data_bucket,
#     glue_database=glue_stack.glue_database,
#     env=env_config,
#     description="Analytics infrastructure for Acme Corp streaming data"
# )
# analytics_stack.add_dependency(glue_stack)

# Add tags to all stacks
for stack in [data_lake_stack, glue_stack]:  # analytics_stack removed for now
    cdk.Tags.of(stack).add("Project", "AcmeStreamingPlatform")
    cdk.Tags.of(stack).add("Environment", "Development")
    cdk.Tags.of(stack).add("ManagedBy", "CDK")

app.synth()