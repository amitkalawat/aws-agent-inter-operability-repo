import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_glue as glue,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput
)
from constructs import Construct
import json

class GlueStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, data_bucket: s3.Bucket, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.data_bucket = data_bucket
        
        # Create Glue database
        self.glue_database = glue.CfnDatabase(
            self,
            "AcmeStreamingDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="acme_streaming_data",
                description="Database for Acme Corp streaming platform data",
                location_uri=f"s3://{data_bucket.bucket_name}/"
            )
        )
        
        # Create Glue role for crawlers
        self.glue_crawler_role = iam.Role(
            self,
            "GlueCrawlerRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
            ]
        )
        
        # Grant S3 permissions to crawler role
        data_bucket.grant_read(self.glue_crawler_role)
        
        # Add inline policy for CloudWatch Logs
        self.glue_crawler_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["arn:aws:logs:*:*:*"]
            )
        )
        
        # Create Glue tables
        self._create_customer_table()
        self._create_title_table()
        self._create_telemetry_table()
        self._create_campaign_table()
        
        # Create Glue crawlers
        self._create_crawlers()
        
        # Outputs
        CfnOutput(
            self,
            "GlueDatabaseName",
            value=self.glue_database.ref,
            description="Name of the Glue database"
        )
    
    def _create_customer_table(self):
        glue.CfnTable(
            self,
            "CustomerTable",
            catalog_id=self.account,
            database_name=self.glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="customers",
                description="Customer data for Acme streaming platform",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet",
                    "compressionType": "snappy"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"s3://{self.data_bucket.bucket_name}/raw/customers/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
                    ),
                    columns=[
                        {"name": "customer_id", "type": "string"},
                        {"name": "email", "type": "string"},
                        {"name": "first_name", "type": "string"},
                        {"name": "last_name", "type": "string"},
                        {"name": "date_of_birth", "type": "date"},
                        {"name": "age_group", "type": "string"},
                        {"name": "subscription_tier", "type": "string"},
                        {"name": "subscription_start_date", "type": "timestamp"},
                        {"name": "subscription_end_date", "type": "timestamp"},  # Can be null for active customers
                        {"name": "country", "type": "string"},
                        {"name": "state", "type": "string"},
                        {"name": "city", "type": "string"},
                        {"name": "timezone", "type": "string"},
                        {"name": "payment_method", "type": "string"},
                        {"name": "monthly_revenue", "type": "double"},
                        {"name": "lifetime_value", "type": "double"},
                        {"name": "is_active", "type": "boolean"},
                        {"name": "acquisition_channel", "type": "string"},
                        {"name": "preferred_genres", "type": "string"},
                        {"name": "created_at", "type": "timestamp"},
                        {"name": "updated_at", "type": "timestamp"}
                    ]
                )
            )
        )
    
    def _create_title_table(self):
        glue.CfnTable(
            self,
            "TitleTable",
            catalog_id=self.account,
            database_name=self.glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="titles",
                description="Title/content data for Acme streaming platform",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet",
                    "compressionType": "snappy"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"s3://{self.data_bucket.bucket_name}/raw/titles/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
                    ),
                    columns=[
                        {"name": "title_id", "type": "string"},
                        {"name": "title_name", "type": "string"},
                        {"name": "title_type", "type": "string"},
                        {"name": "genre", "type": "string"},
                        {"name": "sub_genre", "type": "string"},
                        {"name": "content_rating", "type": "string"},
                        {"name": "release_date", "type": "date"},
                        {"name": "duration_minutes", "type": "int"},
                        {"name": "season_number", "type": "double"},  # Changed to double to handle NaN values
                        {"name": "episode_number", "type": "double"},  # Changed to double to handle NaN values
                        {"name": "production_country", "type": "string"},
                        {"name": "original_language", "type": "string"},
                        {"name": "available_languages", "type": "string"},
                        {"name": "director", "type": "string"},
                        {"name": "cast", "type": "string"},
                        {"name": "production_studio", "type": "string"},
                        {"name": "popularity_score", "type": "double"},
                        {"name": "critical_rating", "type": "double"},
                        {"name": "viewer_rating", "type": "double"},
                        {"name": "budget_millions", "type": "double"},
                        {"name": "revenue_millions", "type": "double"},
                        {"name": "awards_count", "type": "int"},
                        {"name": "is_original", "type": "boolean"},
                        {"name": "licensing_cost", "type": "double"},
                        {"name": "created_at", "type": "timestamp"},
                        {"name": "updated_at", "type": "timestamp"}
                    ]
                )
            )
        )
    
    def _create_telemetry_table(self):
        glue.CfnTable(
            self,
            "TelemetryTable",
            catalog_id=self.account,
            database_name=self.glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="telemetry",
                description="Video telemetry/viewing data",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet",
                    "compressionType": "snappy"
                },
                partition_keys=[
                    {"name": "date", "type": "string"}
                ],
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"s3://{self.data_bucket.bucket_name}/raw/telemetry/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
                    ),
                    columns=[
                        {"name": "event_id", "type": "string"},
                        {"name": "customer_id", "type": "string"},
                        {"name": "title_id", "type": "string"},
                        {"name": "session_id", "type": "string"},
                        {"name": "event_type", "type": "string"},
                        {"name": "event_timestamp", "type": "timestamp"},
                        {"name": "watch_duration_seconds", "type": "int"},
                        {"name": "position_seconds", "type": "int"},
                        {"name": "completion_percentage", "type": "double"},
                        {"name": "device_type", "type": "string"},
                        {"name": "device_id", "type": "string"},
                        {"name": "device_os", "type": "string"},
                        {"name": "app_version", "type": "string"},
                        {"name": "quality", "type": "string"},
                        {"name": "bandwidth_mbps", "type": "double"},
                        {"name": "buffering_events", "type": "int"},
                        {"name": "buffering_duration_seconds", "type": "int"},
                        {"name": "error_count", "type": "int"},
                        {"name": "ip_address", "type": "string"},
                        {"name": "country", "type": "string"},
                        {"name": "state", "type": "string"},
                        {"name": "city", "type": "string"},
                        {"name": "isp", "type": "string"},
                        {"name": "connection_type", "type": "string"}
                    ]
                )
            )
        )
    
    def _create_campaign_table(self):
        glue.CfnTable(
            self,
            "CampaignTable",
            catalog_id=self.account,
            database_name=self.glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="campaigns",
                description="Ad campaign data",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet",
                    "compressionType": "snappy"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"s3://{self.data_bucket.bucket_name}/raw/campaigns/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
                    ),
                    columns=[
                        {"name": "campaign_id", "type": "string"},
                        {"name": "campaign_name", "type": "string"},
                        {"name": "advertiser_id", "type": "string"},
                        {"name": "advertiser_name", "type": "string"},
                        {"name": "industry", "type": "string"},
                        {"name": "campaign_type", "type": "string"},
                        {"name": "objective", "type": "string"},
                        {"name": "start_date", "type": "date"},
                        {"name": "end_date", "type": "date"},
                        {"name": "status", "type": "string"},
                        {"name": "daily_budget", "type": "double"},
                        {"name": "total_budget", "type": "double"},
                        {"name": "spent_amount", "type": "double"},
                        {"name": "target_age_groups", "type": "string"},
                        {"name": "target_genders", "type": "string"},
                        {"name": "target_countries", "type": "string"},
                        {"name": "target_genres", "type": "string"},
                        {"name": "target_subscription_tiers", "type": "string"},
                        {"name": "ad_format", "type": "string"},
                        {"name": "ad_duration_seconds", "type": "int"},
                        {"name": "placement_type", "type": "string"},
                        {"name": "creative_url", "type": "string"},
                        {"name": "landing_page_url", "type": "string"},
                        {"name": "impressions", "type": "bigint"},
                        {"name": "unique_viewers", "type": "bigint"},
                        {"name": "clicks", "type": "bigint"},
                        {"name": "conversions", "type": "bigint"},
                        {"name": "view_through_rate", "type": "double"},
                        {"name": "click_through_rate", "type": "double"},
                        {"name": "conversion_rate", "type": "double"},
                        {"name": "cost_per_mille", "type": "double"},
                        {"name": "cost_per_click", "type": "double"},
                        {"name": "cost_per_conversion", "type": "double"},
                        {"name": "created_at", "type": "timestamp"},
                        {"name": "updated_at", "type": "timestamp"}
                    ]
                )
            )
        )
    
    def _create_crawlers(self):
        # Customer crawler
        glue.CfnCrawler(
            self,
            "CustomerCrawler",
            name="acme-customer-crawler",
            role=self.glue_crawler_role.role_arn,
            database_name=self.glue_database.ref,
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{self.data_bucket.bucket_name}/raw/customers/"
                    )
                ]
            ),
            schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
                update_behavior="UPDATE_IN_DATABASE",
                delete_behavior="LOG"
            )
        )
        
        # Telemetry crawler (with partitions)
        glue.CfnCrawler(
            self,
            "TelemetryCrawler",
            name="acme-telemetry-crawler",
            role=self.glue_crawler_role.role_arn,
            database_name=self.glue_database.ref,
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{self.data_bucket.bucket_name}/raw/telemetry/"
                    )
                ]
            ),
            schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
                update_behavior="UPDATE_IN_DATABASE",
                delete_behavior="LOG"
            )
        )