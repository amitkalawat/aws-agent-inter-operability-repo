import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_athena as athena,
    aws_redshift as redshift,
    aws_iam as iam,
    aws_s3 as s3,
    aws_glue as glue,
    aws_ec2 as ec2,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class AnalyticsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, 
                 data_bucket: s3.Bucket, 
                 glue_database: glue.CfnDatabase, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.data_bucket = data_bucket
        self.glue_database = glue_database
        
        # Create S3 bucket for Athena query results
        self.athena_results_bucket = s3.Bucket(
            self,
            "AthenaResultsBucket",
            bucket_name=f"acme-athena-results-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldQueryResults",
                    expiration=cdk.Duration.days(30)
                )
            ]
        )
        
        # Create Athena workgroup
        self.athena_workgroup = athena.CfnWorkGroup(
            self,
            "AcmeAthenaWorkGroup",
            name="acme-streaming-analytics",
            description="Athena workgroup for Acme streaming data analytics",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.athena_results_bucket.bucket_name}/",
                    encryption_configuration=athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_S3"
                    )
                ),
                enforce_work_group_configuration=True,
                publish_cloud_watch_metrics_enabled=True
            )
        )
        
        # Create VPC for Redshift Serverless
        self.vpc = ec2.Vpc(
            self,
            "RedshiftVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )
        
        # Create security group for Redshift
        self.redshift_security_group = ec2.SecurityGroup(
            self,
            "RedshiftSecurityGroup",
            vpc=self.vpc,
            description="Security group for Redshift Serverless",
            allow_all_outbound=True
        )
        
        # Allow Redshift port from within VPC
        self.redshift_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5439),
            description="Allow Redshift connections from within VPC"
        )
        
        # Create IAM role for Redshift
        self.redshift_role = iam.Role(
            self,
            "RedshiftRole",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
            ]
        )
        
        # Grant Redshift access to data bucket
        self.data_bucket.grant_read(self.redshift_role)
        
        # Add Glue catalog permissions
        self.redshift_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "glue:GetDatabase",
                    "glue:GetTable",
                    "glue:GetTables",
                    "glue:GetPartition",
                    "glue:GetPartitions",
                    "glue:BatchCreatePartition",
                    "glue:BatchDeletePartition",
                    "glue:BatchUpdatePartition"
                ],
                resources=[
                    f"arn:aws:glue:{self.region}:{self.account}:catalog",
                    f"arn:aws:glue:{self.region}:{self.account}:database/{self.glue_database.ref}",
                    f"arn:aws:glue:{self.region}:{self.account}:table/{self.glue_database.ref}/*"
                ]
            )
        )
        
        # Create Redshift Serverless namespace
        self.redshift_namespace = redshift.CfnNamespace(
            self,
            "RedshiftNamespace",
            namespace_name="acme-streaming-analytics",
            db_name="acme_analytics",
            admin_username="admin",
            admin_user_password="<SET_REDSHIFT_ADMIN_PASSWORD>",  # TODO: Use AWS Secrets Manager in production
            default_iam_role_arn=self.redshift_role.role_arn,
            iam_roles=[self.redshift_role.role_arn],
            tags=[
                {"key": "Project", "value": "AcmeStreamingPlatform"}
            ]
        )
        
        # Create Redshift Serverless workgroup
        self.redshift_workgroup = redshift.CfnWorkgroup(
            self,
            "RedshiftWorkgroup",
            workgroup_name="acme-streaming-workgroup",
            namespace_name=self.redshift_namespace.namespace_name,
            base_capacity=32,  # RPUs (Redshift Processing Units)
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.private_subnets],
            security_group_ids=[self.redshift_security_group.security_group_id],
            publicly_accessible=False,
            tags=[
                {"key": "Project", "value": "AcmeStreamingPlatform"}
            ]
        )
        
        self.redshift_workgroup.add_dependency(self.redshift_namespace)
        
        # Create sample Athena named queries
        self._create_athena_queries()
        
        # Outputs
        CfnOutput(
            self,
            "AthenaWorkgroupName",
            value=self.athena_workgroup.name,
            description="Name of the Athena workgroup"
        )
        
        CfnOutput(
            self,
            "AthenaResultsBucket",
            value=self.athena_results_bucket.bucket_name,
            description="S3 bucket for Athena query results"
        )
        
        CfnOutput(
            self,
            "RedshiftNamespaceName",
            value=self.redshift_namespace.namespace_name,
            description="Redshift Serverless namespace name"
        )
        
        CfnOutput(
            self,
            "RedshiftWorkgroupName",
            value=self.redshift_workgroup.workgroup_name,
            description="Redshift Serverless workgroup name"
        )
        
        CfnOutput(
            self,
            "RedshiftEndpoint",
            value=f"{self.redshift_workgroup.workgroup_name}.{self.region}.redshift-serverless.amazonaws.com:5439",
            description="Redshift Serverless endpoint"
        )
    
    def _create_athena_queries(self):
        # Popular content by genre
        athena.CfnNamedQuery(
            self,
            "PopularContentByGenre",
            name="Popular Content by Genre",
            database=self.glue_database.ref,
            work_group=self.athena_workgroup.name,
            query_string="""
-- Popular content by genre
SELECT 
    t.genre,
    t.title_name,
    t.title_type,
    COUNT(DISTINCT tel.customer_id) as unique_viewers,
    COUNT(*) as total_views,
    AVG(tel.completion_percentage) as avg_completion_rate,
    SUM(tel.watch_duration_seconds) / 3600.0 as total_hours_watched
FROM telemetry tel
JOIN titles t ON tel.title_id = t.title_id
WHERE tel.event_type IN ('stop', 'complete')
GROUP BY t.genre, t.title_name, t.title_type
ORDER BY unique_viewers DESC
LIMIT 20;
            """
        )
        
        # Customer churn analysis
        athena.CfnNamedQuery(
            self,
            "CustomerChurnAnalysis",
            name="Customer Churn Analysis",
            database=self.glue_database.ref,
            work_group=self.athena_workgroup.name,
            query_string="""
-- Customer churn analysis by subscription tier
SELECT 
    subscription_tier,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_customers,
    COUNT(CASE WHEN is_active = false THEN 1 END) as churned_customers,
    COUNT(*) as total_customers,
    ROUND(100.0 * COUNT(CASE WHEN is_active = false THEN 1 END) / COUNT(*), 2) as churn_rate,
    AVG(lifetime_value) as avg_lifetime_value
FROM customers
GROUP BY subscription_tier
ORDER BY churn_rate DESC;
            """
        )
        
        # Ad campaign performance
        athena.CfnNamedQuery(
            self,
            "AdCampaignPerformance",
            name="Ad Campaign Performance Analysis",
            database=self.glue_database.ref,
            work_group=self.athena_workgroup.name,
            query_string="""
-- Top performing ad campaigns by ROI
WITH campaign_roi AS (
    SELECT 
        campaign_name,
        advertiser_name,
        campaign_type,
        status,
        impressions,
        clicks,
        conversions,
        spent_amount,
        CASE 
            WHEN conversions > 0 THEN 
                ROUND((conversions * 50.0 - spent_amount) / spent_amount * 100, 2)
            ELSE -100 
        END as roi_percentage,
        click_through_rate,
        conversion_rate
    FROM campaigns
    WHERE spent_amount > 0
)
SELECT * FROM campaign_roi
ORDER BY roi_percentage DESC
LIMIT 20;
            """
        )