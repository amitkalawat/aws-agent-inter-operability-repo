import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct

class DataLakeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create S3 bucket for data lake
        self.data_bucket = s3.Bucket(
            self,
            "DataLakeBucket",
            bucket_name=f"acme-streaming-data-lake-{self.account}-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  # Change to RETAIN for production
            auto_delete_objects=True,  # Remove for production
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToIA",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                ),
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    noncurrent_version_expiration=Duration.days(30),
                    abort_incomplete_multipart_upload_after=Duration.days(7)
                )
            ],
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.HEAD,
                        s3.HttpMethods.PUT
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=3000
                )
            ]
        )
        
        # Create folder structure in S3
        self._create_folder_structure()
        
        # Create IAM role for data access
        self.data_access_role = iam.Role(
            self,
            "DataAccessRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("glue.amazonaws.com"),
                iam.ServicePrincipal("athena.amazonaws.com"),
                iam.ServicePrincipal("redshift.amazonaws.com")
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
            ]
        )
        
        # Grant read/write permissions to the role
        self.data_bucket.grant_read_write(self.data_access_role)
        
        # Create a bucket policy for cross-service access
        bucket_policy = s3.BucketPolicy(
            self,
            "DataLakeBucketPolicy",
            bucket=self.data_bucket
        )
        
        bucket_policy.document.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ServicePrincipal("athena.amazonaws.com"),
                    iam.ServicePrincipal("glue.amazonaws.com"),
                    iam.ServicePrincipal("redshift.amazonaws.com")
                ],
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                resources=[
                    self.data_bucket.bucket_arn,
                    f"{self.data_bucket.bucket_arn}/*"
                ]
            )
        )
        
        # Outputs
        CfnOutput(
            self,
            "DataBucketName",
            value=self.data_bucket.bucket_name,
            description="Name of the S3 data lake bucket"
        )
        
        CfnOutput(
            self,
            "DataBucketArn",
            value=self.data_bucket.bucket_arn,
            description="ARN of the S3 data lake bucket"
        )
        
        CfnOutput(
            self,
            "DataAccessRoleArn",
            value=self.data_access_role.role_arn,
            description="ARN of the data access IAM role"
        )
    
    def _create_folder_structure(self):
        # Note: S3 doesn't have real folders, but we can create zero-byte objects
        # with trailing slashes to simulate folder structure in the console
        folders = [
            "raw/customers/",
            "raw/titles/",
            "raw/telemetry/",
            "raw/campaigns/",
            "processed/customers/",
            "processed/titles/",
            "processed/telemetry/",
            "processed/campaigns/",
            "analytics/reports/",
            "analytics/dashboards/",
            "temp/"
        ]
        
        # In practice, these folders will be created when data is uploaded
        # This is just for documentation purposes