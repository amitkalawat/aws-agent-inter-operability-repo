"""
ACME Telemetry Pipeline - Networking Stack
Optional stack for creating VPC infrastructure if not using existing VPC
"""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    CfnOutput
)
from constructs import Construct

class NetworkingStack(Stack):
    """Optional networking stack for ACME telemetry pipeline"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create VPC with public and private subnets
        self.vpc = ec2.Vpc(
            self, "TelemetryVPC",
            vpc_name="acme-telemetry-vpc",
            max_azs=3,
            nat_gateways=1,  # Single NAT Gateway for cost optimization
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=24
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        
        # VPC Endpoints for AWS services (cost optimization)
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        
        # Optional: Add VPC endpoints for other services
        # Uncomment if needed to reduce NAT Gateway costs
        """
        self.vpc.add_interface_endpoint(
            "LambdaEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.LAMBDA
        )
        
        self.vpc.add_interface_endpoint(
            "KafkaEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.KAFKA
        )
        
        self.vpc.add_interface_endpoint(
            "FirehoseEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.KINESIS_FIREHOSE
        )
        """
        
        # Outputs
        CfnOutput(
            self, "VPCId",
            value=self.vpc.vpc_id,
            description="VPC ID for the telemetry pipeline"
        )
        
        CfnOutput(
            self, "PrivateSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            description="Private subnet IDs"
        )
        
        CfnOutput(
            self, "PublicSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="Public subnet IDs"
        )