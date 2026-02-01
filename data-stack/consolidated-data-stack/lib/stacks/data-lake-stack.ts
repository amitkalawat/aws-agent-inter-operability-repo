import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as glue from 'aws-cdk-lib/aws-glue';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { Config } from '../config';

export class DataLakeStack extends cdk.Stack {
  public readonly dataBucket: s3.Bucket;
  public readonly glueDatabase: glue.CfnDatabase;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 bucket for telemetry data
    this.dataBucket = new s3.Bucket(this, 'DataBucket', {
      bucketName: `${Config.s3.dataBucketName}-${this.account}-${this.region}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      lifecycleRules: [
        {
          id: 'MoveToIA',
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30),
            },
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: cdk.Duration.days(90),
            },
          ],
        },
        {
          id: 'DeleteOldVersions',
          noncurrentVersionExpiration: cdk.Duration.days(30),
        },
        {
          id: 'AbortIncompleteUploads',
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(7),
        },
      ],
    });

    // Glue database
    this.glueDatabase = new glue.CfnDatabase(this, 'GlueDatabase', {
      catalogId: this.account,
      databaseInput: {
        name: Config.glue.databaseName,
        description: 'ACME video streaming telemetry data',
      },
    });

    // Glue table for streaming events
    const glueTable = new glue.CfnTable(this, 'StreamingEventsTable', {
      catalogId: this.account,
      databaseName: Config.glue.databaseName,
      tableInput: {
        name: Config.glue.tableName,
        description: 'Video streaming telemetry events',
        tableType: 'EXTERNAL_TABLE',
        parameters: {
          'classification': 'parquet',
          'parquet.compression': 'SNAPPY',
        },
        storageDescriptor: {
          location: `s3://${this.dataBucket.bucketName}/telemetry/`,
          inputFormat: 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
          outputFormat: 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
          serdeInfo: {
            serializationLibrary: 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
          },
          columns: [
            { name: 'event_id', type: 'string' },
            { name: 'event_type', type: 'string' },
            { name: 'event_timestamp', type: 'string' },
            { name: 'customer_id', type: 'string' },
            { name: 'title_id', type: 'string' },
            { name: 'session_id', type: 'string' },
            { name: 'device_id', type: 'string' },
            { name: 'title_type', type: 'string' },
            { name: 'device_type', type: 'string' },
            { name: 'device_os', type: 'string' },
            { name: 'app_version', type: 'string' },
            { name: 'quality', type: 'string' },
            { name: 'bandwidth_mbps', type: 'double' },
            { name: 'buffering_events', type: 'int' },
            { name: 'buffering_duration_seconds', type: 'double' },
            { name: 'error_count', type: 'int' },
            { name: 'watch_duration_seconds', type: 'int' },
            { name: 'position_seconds', type: 'int' },
            { name: 'completion_percentage', type: 'double' },
            { name: 'ip_address', type: 'string' },
            { name: 'isp', type: 'string' },
            { name: 'connection_type', type: 'string' },
            { name: 'country', type: 'string' },
            { name: 'state', type: 'string' },
            { name: 'city', type: 'string' },
          ],
        },
        partitionKeys: [
          { name: 'year', type: 'string' },
          { name: 'month', type: 'string' },
          { name: 'day', type: 'string' },
          { name: 'hour', type: 'string' },
        ],
      },
    });
    glueTable.addDependency(this.glueDatabase);

    // IAM role for Athena/Glue access
    const dataAccessRole = new iam.Role(this, 'DataAccessRole', {
      roleName: `${Config.prefix}-data-access-role`,
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal('glue.amazonaws.com'),
        new iam.ServicePrincipal('athena.amazonaws.com')
      ),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSGlueServiceRole'),
      ],
    });

    this.dataBucket.grantReadWrite(dataAccessRole);

    // Outputs
    new cdk.CfnOutput(this, 'DataBucketName', { value: this.dataBucket.bucketName });
    new cdk.CfnOutput(this, 'GlueDatabaseName', { value: Config.glue.databaseName });
  }
}
