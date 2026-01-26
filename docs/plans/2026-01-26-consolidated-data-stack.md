# Consolidated Data Stack Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate all 4 data-stack repos into a single TypeScript CDK stack for unified deployment.

**Architecture:** Single CDK app with 4 nested stacks sharing a common VPC. MSK Cluster is the foundation, feeding Lambda generators → Firehose → S3 Data Lake → Glue Catalog. Dashboard consumes MSK events via WebSocket. All resources use consistent naming with environment prefix.

**Tech Stack:** TypeScript CDK 2.x, Node.js 18.x, Python 3.11 (Lambdas), Amazon MSK, Kinesis Firehose, S3, Glue, Athena, API Gateway WebSocket, DynamoDB, CloudFront

---

## Dependency Chain

```
NetworkStack (VPC, Subnets, Security Groups)
       ↓
MskStack (Kafka Cluster, Topics)
       ↓
    ┌──┴──┐
    ↓     ↓
DataGenStack          DashboardStack
(Lambdas, Firehose)   (WebSocket, Consumer)
       ↓
DataLakeStack (S3, Glue, Athena)
```

---

## Task 1: Initialize CDK Project

**Files:**
- Create: `data-stack/consolidated-data-stack/`
- Create: `data-stack/consolidated-data-stack/bin/app.ts`
- Create: `data-stack/consolidated-data-stack/lib/config.ts`
- Create: `data-stack/consolidated-data-stack/package.json`
- Create: `data-stack/consolidated-data-stack/tsconfig.json`
- Create: `data-stack/consolidated-data-stack/cdk.json`

**Step 1: Create project directory structure**

```bash
mkdir -p data-stack/consolidated-data-stack/{bin,lib/{stacks,constructs},lambda/{generator,producer,consumer,websocket}}
```

**Step 2: Create package.json**

Create `data-stack/consolidated-data-stack/package.json`:
```json
{
  "name": "consolidated-data-stack",
  "version": "1.0.0",
  "scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "cdk": "cdk",
    "deploy": "cdk deploy --all",
    "destroy": "cdk destroy --all",
    "synth": "cdk synth"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "typescript": "~5.3.3",
    "aws-cdk": "^2.150.0"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.150.0",
    "constructs": "^10.3.0"
  }
}
```

**Step 3: Create tsconfig.json**

Create `data-stack/consolidated-data-stack/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "declaration": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": false,
    "inlineSourceMap": true,
    "inlineSources": true,
    "experimentalDecorators": true,
    "strictPropertyInitialization": false,
    "outDir": "./dist",
    "rootDir": "."
  },
  "exclude": ["node_modules", "cdk.out", "dist"]
}
```

**Step 4: Create cdk.json**

Create `data-stack/consolidated-data-stack/cdk.json`:
```json
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts",
  "watch": {
    "include": ["**"],
    "exclude": ["node_modules", "cdk.out", "**/*.d.ts", "**/*.js"]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target-partitions": ["aws"]
  }
}
```

**Step 5: Create config.ts**

Create `data-stack/consolidated-data-stack/lib/config.ts`:
```typescript
export const Config = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'us-west-2',
  },
  prefix: 'acme-data',
  msk: {
    clusterName: 'acme-msk-cluster',
    kafkaVersion: '3.5.1',
    brokerInstanceType: 'kafka.m5.large',
    brokerCount: 3,
    ebsVolumeSize: 100,
    topics: {
      telemetry: 'acme-telemetry',
    },
  },
  s3: {
    dataBucketName: 'acme-telemetry-data',
    logsBucketName: 'acme-msk-logs',
  },
  lambda: {
    generatorMemory: 256,
    producerMemory: 512,
    consumerMemory: 512,
    timeout: 300,
  },
  glue: {
    databaseName: 'acme_telemetry',
    tableName: 'streaming_events',
  },
  firehose: {
    bufferInterval: 60,
    bufferSize: 5,
  },
};
```

**Step 6: Create CDK app entry point**

Create `data-stack/consolidated-data-stack/bin/app.ts`:
```typescript
#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { Config } from '../lib/config';
import { NetworkStack } from '../lib/stacks/network-stack';
import { MskStack } from '../lib/stacks/msk-stack';
import { DataGenStack } from '../lib/stacks/data-gen-stack';
import { DataLakeStack } from '../lib/stacks/data-lake-stack';
import { DashboardStack } from '../lib/stacks/dashboard-stack';

const app = new cdk.App();

const networkStack = new NetworkStack(app, 'AcmeNetworkStack', {
  env: Config.env,
});

const mskStack = new MskStack(app, 'AcmeMskStack', {
  env: Config.env,
  vpc: networkStack.vpc,
  mskSecurityGroup: networkStack.mskSecurityGroup,
});
mskStack.addDependency(networkStack);

const dataLakeStack = new DataLakeStack(app, 'AcmeDataLakeStack', {
  env: Config.env,
});

const dataGenStack = new DataGenStack(app, 'AcmeDataGenStack', {
  env: Config.env,
  vpc: networkStack.vpc,
  mskCluster: mskStack.cluster,
  mskSecurityGroup: networkStack.mskSecurityGroup,
  dataBucket: dataLakeStack.dataBucket,
});
dataGenStack.addDependency(mskStack);
dataGenStack.addDependency(dataLakeStack);

const dashboardStack = new DashboardStack(app, 'AcmeDashboardStack', {
  env: Config.env,
  vpc: networkStack.vpc,
  mskCluster: mskStack.cluster,
  mskSecurityGroup: networkStack.mskSecurityGroup,
});
dashboardStack.addDependency(mskStack);

app.synth();
```

**Step 7: Install dependencies and verify**

```bash
cd data-stack/consolidated-data-stack && npm install
```

**Step 8: Commit**

```bash
git add data-stack/consolidated-data-stack/
git commit -m "feat: initialize consolidated data stack CDK project"
```

---

## Task 2: Create Network Stack

**Files:**
- Create: `data-stack/consolidated-data-stack/lib/stacks/network-stack.ts`

**Step 1: Create network stack with VPC and security groups**

Create `data-stack/consolidated-data-stack/lib/stacks/network-stack.ts`:
```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { Config } from '../config';

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.IVpc;
  public readonly mskSecurityGroup: ec2.SecurityGroup;
  public readonly lambdaSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create VPC with public and private subnets
    this.vpc = new ec2.Vpc(this, 'AcmeVpc', {
      vpcName: `${Config.prefix}-vpc`,
      maxAzs: 3,
      natGateways: 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
    });

    // Security group for MSK cluster
    this.mskSecurityGroup = new ec2.SecurityGroup(this, 'MskSecurityGroup', {
      vpc: this.vpc,
      securityGroupName: `${Config.prefix}-msk-sg`,
      description: 'Security group for MSK cluster',
      allowAllOutbound: true,
    });

    // Security group for Lambda functions
    this.lambdaSecurityGroup = new ec2.SecurityGroup(this, 'LambdaSecurityGroup', {
      vpc: this.vpc,
      securityGroupName: `${Config.prefix}-lambda-sg`,
      description: 'Security group for Lambda functions',
      allowAllOutbound: true,
    });

    // Allow Lambda to connect to MSK (SASL/IAM port)
    this.mskSecurityGroup.addIngressRule(
      this.lambdaSecurityGroup,
      ec2.Port.tcp(9098),
      'Allow Lambda SASL/IAM access to MSK'
    );

    // Allow MSK internal communication
    this.mskSecurityGroup.addIngressRule(
      this.mskSecurityGroup,
      ec2.Port.allTraffic(),
      'Allow MSK internal communication'
    );

    // Outputs
    new cdk.CfnOutput(this, 'VpcId', { value: this.vpc.vpcId });
    new cdk.CfnOutput(this, 'MskSecurityGroupId', { value: this.mskSecurityGroup.securityGroupId });
  }
}
```

**Step 2: Verify TypeScript compiles**

```bash
cd data-stack/consolidated-data-stack && npm run build
```

**Step 3: Commit**

```bash
git add data-stack/consolidated-data-stack/lib/stacks/network-stack.ts
git commit -m "feat: add network stack with VPC and security groups"
```

---

## Task 3: Create MSK Stack

**Files:**
- Create: `data-stack/consolidated-data-stack/lib/stacks/msk-stack.ts`
- Reference: `data-stack/ibc2025-data-gen-msk-repo-v2/lib/constructs/msk-cluster.ts`

**Step 1: Create MSK stack**

Create `data-stack/consolidated-data-stack/lib/stacks/msk-stack.ts`:
```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as msk from 'aws-cdk-lib/aws-msk';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cr from 'aws-cdk-lib/custom-resources';
import { Construct } from 'constructs';
import { Config } from '../config';

export interface MskStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  mskSecurityGroup: ec2.SecurityGroup;
}

export class MskStack extends cdk.Stack {
  public readonly cluster: msk.CfnCluster;
  public readonly bootstrapServers: string;
  public readonly logGroup: logs.LogGroup;

  constructor(scope: Construct, id: string, props: MskStackProps) {
    super(scope, id, props);

    // S3 bucket for MSK logs
    const logsBucket = new s3.Bucket(this, 'MskLogsBucket', {
      bucketName: `${Config.s3.logsBucketName}-${this.account}-${this.region}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // CloudWatch log group for MSK
    this.logGroup = new logs.LogGroup(this, 'MskLogGroup', {
      logGroupName: `/aws/msk/${Config.msk.clusterName}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Get private subnet IDs
    const privateSubnets = props.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    }).subnetIds;

    // MSK Cluster configuration
    this.cluster = new msk.CfnCluster(this, 'MskCluster', {
      clusterName: Config.msk.clusterName,
      kafkaVersion: Config.msk.kafkaVersion,
      numberOfBrokerNodes: Config.msk.brokerCount,
      brokerNodeGroupInfo: {
        instanceType: Config.msk.brokerInstanceType,
        clientSubnets: privateSubnets,
        securityGroups: [props.mskSecurityGroup.securityGroupId],
        storageInfo: {
          ebsStorageInfo: {
            volumeSize: Config.msk.ebsVolumeSize,
          },
        },
      },
      clientAuthentication: {
        sasl: {
          iam: { enabled: true },
        },
      },
      encryptionInfo: {
        encryptionInTransit: {
          clientBroker: 'TLS',
          inCluster: true,
        },
      },
      enhancedMonitoring: 'PER_TOPIC_PER_BROKER',
      loggingInfo: {
        brokerLogs: {
          cloudWatchLogs: {
            enabled: true,
            logGroup: this.logGroup.logGroupName,
          },
          s3: {
            enabled: true,
            bucket: logsBucket.bucketName,
            prefix: 'msk-logs/',
          },
        },
      },
    });

    // Custom resource to get bootstrap servers
    const getBootstrapServers = new cr.AwsCustomResource(this, 'GetBootstrapServers', {
      onCreate: {
        service: 'Kafka',
        action: 'getBootstrapBrokers',
        parameters: {
          ClusterArn: this.cluster.attrArn,
        },
        physicalResourceId: cr.PhysicalResourceId.of('BootstrapServers'),
      },
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({
        resources: [this.cluster.attrArn],
      }),
    });
    getBootstrapServers.node.addDependency(this.cluster);

    this.bootstrapServers = getBootstrapServers.getResponseField('BootstrapBrokerStringSaslIam');

    // Outputs
    new cdk.CfnOutput(this, 'MskClusterArn', { value: this.cluster.attrArn });
    new cdk.CfnOutput(this, 'BootstrapServers', { value: this.bootstrapServers });
  }
}
```

**Step 2: Verify TypeScript compiles**

```bash
cd data-stack/consolidated-data-stack && npm run build
```

**Step 3: Commit**

```bash
git add data-stack/consolidated-data-stack/lib/stacks/msk-stack.ts
git commit -m "feat: add MSK stack with Kafka cluster"
```

---

## Task 4: Create Data Lake Stack

**Files:**
- Create: `data-stack/consolidated-data-stack/lib/stacks/data-lake-stack.ts`
- Reference: `data-stack/ibc2025-mcp-data-generation-repo/cdk/stacks/data_lake_stack.py`
- Reference: `data-stack/ibc2025-mcp-data-generation-repo/cdk/stacks/glue_stack.py`

**Step 1: Create data lake stack with S3 and Glue**

Create `data-stack/consolidated-data-stack/lib/stacks/data-lake-stack.ts`:
```typescript
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
          'classification': 'json',
          'compressionType': 'gzip',
        },
        storageDescriptor: {
          location: `s3://${this.dataBucket.bucketName}/telemetry/`,
          inputFormat: 'org.apache.hadoop.mapred.TextInputFormat',
          outputFormat: 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
          serdeInfo: {
            serializationLibrary: 'org.openx.data.jsonserde.JsonSerDe',
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
```

**Step 2: Verify TypeScript compiles**

```bash
cd data-stack/consolidated-data-stack && npm run build
```

**Step 3: Commit**

```bash
git add data-stack/consolidated-data-stack/lib/stacks/data-lake-stack.ts
git commit -m "feat: add data lake stack with S3 and Glue catalog"
```

---

## Task 5: Create Data Generator Lambda Functions

**Files:**
- Create: `data-stack/consolidated-data-stack/lambda/generator/handler.py`
- Create: `data-stack/consolidated-data-stack/lambda/generator/requirements.txt`
- Create: `data-stack/consolidated-data-stack/lambda/producer/handler.py`
- Create: `data-stack/consolidated-data-stack/lambda/producer/requirements.txt`
- Reference: `data-stack/ibc2025-data-gen-acme-video-telemetry-synthetic/lambda/telemetry_generator/handler.py`

**Step 1: Create generator Lambda handler**

Create `data-stack/consolidated-data-stack/lambda/generator/handler.py`:
```python
import json
import os
import random
import uuid
from datetime import datetime
from typing import Any

import boto3

# Event types and their probabilities
EVENT_TYPES = ['start', 'pause', 'resume', 'stop', 'complete']
EVENT_WEIGHTS = [0.30, 0.15, 0.15, 0.25, 0.15]

DEVICE_TYPES = ['mobile', 'web', 'tv', 'tablet']
DEVICE_WEIGHTS = [0.35, 0.30, 0.25, 0.10]

QUALITY_LEVELS = ['SD', 'HD', '4K']
QUALITY_WEIGHTS = [0.20, 0.50, 0.30]

TITLE_TYPES = ['movie', 'series', 'documentary']
TITLE_WEIGHTS = [0.60, 0.30, 0.10]

CONNECTION_TYPES = ['wifi', 'mobile', 'fiber', 'cable', 'dsl', 'satellite']
ISPS = ['Comcast', 'AT&T', 'Verizon', 'Spectrum', 'Cox', 'CenturyLink']

COUNTRIES = ['US']
US_STATES = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
CITIES = {
    'CA': ['Los Angeles', 'San Francisco', 'San Diego'],
    'TX': ['Houston', 'Dallas', 'Austin'],
    'FL': ['Miami', 'Orlando', 'Tampa'],
    'NY': ['New York', 'Buffalo', 'Albany'],
}

lambda_client = boto3.client('lambda')


def generate_event() -> dict[str, Any]:
    """Generate a single telemetry event."""
    state = random.choice(US_STATES)
    city = random.choice(CITIES.get(state, ['Unknown']))

    event = {
        'event_id': str(uuid.uuid4()),
        'event_type': random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS)[0],
        'event_timestamp': datetime.utcnow().isoformat() + 'Z',
        'customer_id': f'cust_{random.randint(1, 100000):06d}',
        'title_id': f'title_{random.randint(1, 10000):05d}',
        'session_id': str(uuid.uuid4()),
        'device_id': str(uuid.uuid4()),
        'title_type': random.choices(TITLE_TYPES, weights=TITLE_WEIGHTS)[0],
        'device_type': random.choices(DEVICE_TYPES, weights=DEVICE_WEIGHTS)[0],
        'device_os': random.choice(['iOS', 'Android', 'Windows', 'macOS', 'Linux', 'tvOS', 'Roku']),
        'app_version': f'{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}',
        'quality': random.choices(QUALITY_LEVELS, weights=QUALITY_WEIGHTS)[0],
        'bandwidth_mbps': round(random.uniform(5.0, 100.0), 2),
        'buffering_events': random.randint(0, 5),
        'buffering_duration_seconds': round(random.uniform(0, 30.0), 2),
        'error_count': random.randint(0, 2),
        'watch_duration_seconds': random.randint(0, 7200),
        'position_seconds': random.randint(0, 7200),
        'completion_percentage': round(random.uniform(0, 100.0), 2),
        'ip_address': f'{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}',
        'isp': random.choice(ISPS),
        'connection_type': random.choice(CONNECTION_TYPES),
        'country': 'US',
        'state': state,
        'city': city,
    }
    return event


def handler(event: dict, context: Any) -> dict:
    """Lambda handler - generates events and invokes producer."""
    batch_size = int(os.environ.get('BATCH_SIZE', '1000'))
    producer_function = os.environ.get('PRODUCER_FUNCTION_NAME')

    events = [generate_event() for _ in range(batch_size)]

    # Invoke producer Lambda with batch
    if producer_function:
        lambda_client.invoke(
            FunctionName=producer_function,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({'events': events}),
        )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Generated {len(events)} events',
            'batch_size': batch_size,
        }),
    }
```

**Step 2: Create generator requirements.txt**

Create `data-stack/consolidated-data-stack/lambda/generator/requirements.txt`:
```
boto3>=1.34.0
```

**Step 3: Create producer Lambda handler**

Create `data-stack/consolidated-data-stack/lambda/producer/handler.py`:
```python
import json
import os
from typing import Any

from aws_msk_iam_sasl_signer import MSKAuthTokenProvider
from kafka import KafkaProducer


def get_kafka_producer() -> KafkaProducer:
    """Create Kafka producer with IAM authentication."""
    bootstrap_servers = os.environ['BOOTSTRAP_SERVERS']

    def msk_token_provider():
        token, _ = MSKAuthTokenProvider.generate_auth_token(os.environ['AWS_REGION'])
        return token

    return KafkaProducer(
        bootstrap_servers=bootstrap_servers.split(','),
        security_protocol='SASL_SSL',
        sasl_mechanism='OAUTHBEARER',
        sasl_oauth_token_provider=msk_token_provider,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3,
    )


producer = None


def handler(event: dict, context: Any) -> dict:
    """Lambda handler - produces events to MSK."""
    global producer

    if producer is None:
        producer = get_kafka_producer()

    topic = os.environ.get('KAFKA_TOPIC', 'acme-telemetry')
    events = event.get('events', [])

    for evt in events:
        producer.send(topic, value=evt)

    producer.flush()

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Produced {len(events)} events to {topic}',
        }),
    }
```

**Step 4: Create producer requirements.txt**

Create `data-stack/consolidated-data-stack/lambda/producer/requirements.txt`:
```
boto3>=1.34.0
kafka-python>=2.0.2
aws-msk-iam-sasl-signer-python>=1.0.1
```

**Step 5: Commit**

```bash
git add data-stack/consolidated-data-stack/lambda/
git commit -m "feat: add generator and producer Lambda functions"
```

---

## Task 6: Create Data Generation Stack

**Files:**
- Create: `data-stack/consolidated-data-stack/lib/stacks/data-gen-stack.ts`
- Reference: `data-stack/ibc2025-data-gen-acme-video-telemetry-synthetic/cdk/stacks/telemetry_pipeline_stack.py`

**Step 1: Create data generation stack**

Create `data-stack/consolidated-data-stack/lib/stacks/data-gen-stack.ts`:
```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as firehose from 'aws-cdk-lib/aws-kinesisfirehose';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as msk from 'aws-cdk-lib/aws-msk';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { Config } from '../config';
import * as path from 'path';

export interface DataGenStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  mskCluster: msk.CfnCluster;
  mskSecurityGroup: ec2.SecurityGroup;
  dataBucket: s3.Bucket;
}

export class DataGenStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DataGenStackProps) {
    super(scope, id, props);

    // Lambda security group
    const lambdaSg = new ec2.SecurityGroup(this, 'LambdaSecurityGroup', {
      vpc: props.vpc,
      description: 'Security group for data gen Lambdas',
      allowAllOutbound: true,
    });

    props.mskSecurityGroup.addIngressRule(
      lambdaSg,
      ec2.Port.tcp(9098),
      'Allow Lambda to connect to MSK'
    );

    // Producer Lambda
    const producerRole = new iam.Role(this, 'ProducerRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
      ],
    });

    producerRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'kafka-cluster:Connect',
        'kafka-cluster:WriteData',
        'kafka-cluster:DescribeTopic',
        'kafka-cluster:CreateTopic',
      ],
      resources: ['*'],
    }));

    const producerFn = new lambda.Function(this, 'ProducerFunction', {
      functionName: `${Config.prefix}-producer`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/producer')),
      timeout: cdk.Duration.seconds(Config.lambda.timeout),
      memorySize: Config.lambda.producerMemory,
      role: producerRole,
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [lambdaSg],
      environment: {
        BOOTSTRAP_SERVERS: cdk.Fn.getAtt(props.mskCluster.logicalId, 'BootstrapBrokers').toString(),
        KAFKA_TOPIC: Config.msk.topics.telemetry,
        AWS_REGION: this.region,
      },
    });

    // Generator Lambda
    const generatorRole = new iam.Role(this, 'GeneratorRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    generatorRole.addToPolicy(new iam.PolicyStatement({
      actions: ['lambda:InvokeFunction'],
      resources: [producerFn.functionArn],
    }));

    const generatorFn = new lambda.Function(this, 'GeneratorFunction', {
      functionName: `${Config.prefix}-generator`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/generator')),
      timeout: cdk.Duration.seconds(60),
      memorySize: Config.lambda.generatorMemory,
      role: generatorRole,
      environment: {
        BATCH_SIZE: '1000',
        PRODUCER_FUNCTION_NAME: producerFn.functionName,
      },
    });

    // EventBridge rule to trigger generator every 5 minutes
    const rule = new events.Rule(this, 'GeneratorSchedule', {
      ruleName: `${Config.prefix}-generator-schedule`,
      schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
    });
    rule.addTarget(new targets.LambdaFunction(generatorFn));

    // Firehose delivery stream for MSK to S3
    const firehoseRole = new iam.Role(this, 'FirehoseRole', {
      assumedBy: new iam.ServicePrincipal('firehose.amazonaws.com'),
    });

    props.dataBucket.grantReadWrite(firehoseRole);

    firehoseRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'kafka:DescribeCluster',
        'kafka:GetBootstrapBrokers',
        'kafka-cluster:Connect',
        'kafka-cluster:ReadData',
        'kafka-cluster:DescribeTopic',
        'kafka-cluster:DescribeGroup',
      ],
      resources: ['*'],
    }));

    const firehoseLogGroup = new logs.LogGroup(this, 'FirehoseLogGroup', {
      logGroupName: `/aws/firehose/${Config.prefix}-delivery`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const deliveryStream = new firehose.CfnDeliveryStream(this, 'DeliveryStream', {
      deliveryStreamName: `${Config.prefix}-delivery-stream`,
      deliveryStreamType: 'MSKAsSource',
      mskSourceConfiguration: {
        mskClusterArn: props.mskCluster.attrArn,
        topicName: Config.msk.topics.telemetry,
        authenticationConfiguration: {
          connectivity: 'PRIVATE',
          roleArn: firehoseRole.roleArn,
        },
      },
      extendedS3DestinationConfiguration: {
        bucketArn: props.dataBucket.bucketArn,
        roleArn: firehoseRole.roleArn,
        prefix: 'telemetry/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/',
        errorOutputPrefix: 'errors/',
        bufferingHints: {
          intervalInSeconds: Config.firehose.bufferInterval,
          sizeInMBs: Config.firehose.bufferSize,
        },
        compressionFormat: 'GZIP',
        cloudWatchLoggingOptions: {
          enabled: true,
          logGroupName: firehoseLogGroup.logGroupName,
          logStreamName: 'delivery',
        },
      },
    });

    // Outputs
    new cdk.CfnOutput(this, 'GeneratorFunctionArn', { value: generatorFn.functionArn });
    new cdk.CfnOutput(this, 'ProducerFunctionArn', { value: producerFn.functionArn });
    new cdk.CfnOutput(this, 'DeliveryStreamName', { value: deliveryStream.deliveryStreamName! });
  }
}
```

**Step 2: Verify TypeScript compiles**

```bash
cd data-stack/consolidated-data-stack && npm run build
```

**Step 3: Commit**

```bash
git add data-stack/consolidated-data-stack/lib/stacks/data-gen-stack.ts
git commit -m "feat: add data generation stack with Lambdas and Firehose"
```

---

## Task 7: Create Dashboard Lambda Functions

**Files:**
- Create: `data-stack/consolidated-data-stack/lambda/websocket/connect.js`
- Create: `data-stack/consolidated-data-stack/lambda/websocket/disconnect.js`
- Create: `data-stack/consolidated-data-stack/lambda/websocket/default.js`
- Create: `data-stack/consolidated-data-stack/lambda/consumer/handler.js`
- Reference: `data-stack/ibc2025-data-gen-acme-video-telemetry-dashboard/telemetry-dashboard-cdk/`

**Step 1: Create WebSocket connect handler**

Create `data-stack/consolidated-data-stack/lambda/websocket/connect.js`:
```javascript
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { PutCommand, DynamoDBDocumentClient } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
  const connectionId = event.requestContext.connectionId;
  const tableName = process.env.CONNECTIONS_TABLE;

  try {
    await docClient.send(new PutCommand({
      TableName: tableName,
      Item: {
        connectionId,
        connectedAt: new Date().toISOString(),
        ttl: Math.floor(Date.now() / 1000) + 86400, // 24 hours
      },
    }));

    return { statusCode: 200, body: 'Connected' };
  } catch (error) {
    console.error('Connect error:', error);
    return { statusCode: 500, body: 'Failed to connect' };
  }
};
```

**Step 2: Create WebSocket disconnect handler**

Create `data-stack/consolidated-data-stack/lambda/websocket/disconnect.js`:
```javascript
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DeleteCommand, DynamoDBDocumentClient } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
  const connectionId = event.requestContext.connectionId;
  const tableName = process.env.CONNECTIONS_TABLE;

  try {
    await docClient.send(new DeleteCommand({
      TableName: tableName,
      Key: { connectionId },
    }));

    return { statusCode: 200, body: 'Disconnected' };
  } catch (error) {
    console.error('Disconnect error:', error);
    return { statusCode: 500, body: 'Failed to disconnect' };
  }
};
```

**Step 3: Create WebSocket default handler**

Create `data-stack/consolidated-data-stack/lambda/websocket/default.js`:
```javascript
exports.handler = async (event) => {
  console.log('Default route:', JSON.stringify(event));
  return { statusCode: 200, body: 'Message received' };
};
```

**Step 4: Create MSK consumer handler**

Create `data-stack/consolidated-data-stack/lambda/consumer/handler.js`:
```javascript
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { ScanCommand, DynamoDBDocumentClient } = require('@aws-sdk/lib-dynamodb');
const { ApiGatewayManagementApiClient, PostToConnectionCommand } = require('@aws-sdk/client-apigatewaymanagementapi');

const ddbClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(ddbClient);

exports.handler = async (event) => {
  const tableName = process.env.CONNECTIONS_TABLE;
  const wsEndpoint = process.env.WEBSOCKET_ENDPOINT;

  if (!wsEndpoint) {
    console.error('WEBSOCKET_ENDPOINT not set');
    return { statusCode: 500 };
  }

  const apiClient = new ApiGatewayManagementApiClient({
    endpoint: wsEndpoint,
  });

  // Parse MSK records
  const messages = [];
  for (const [topic, partitions] of Object.entries(event.records || {})) {
    for (const record of partitions) {
      try {
        const value = Buffer.from(record.value, 'base64').toString('utf-8');
        messages.push(JSON.parse(value));
      } catch (e) {
        console.error('Failed to parse record:', e);
      }
    }
  }

  if (messages.length === 0) {
    return { statusCode: 200, body: 'No messages' };
  }

  // Get all connections
  let connections = [];
  try {
    const result = await docClient.send(new ScanCommand({ TableName: tableName }));
    connections = result.Items || [];
  } catch (error) {
    console.error('Failed to scan connections:', error);
    return { statusCode: 500 };
  }

  // Broadcast to all connections
  const payload = JSON.stringify({ type: 'telemetry', data: messages });

  await Promise.all(connections.map(async ({ connectionId }) => {
    try {
      await apiClient.send(new PostToConnectionCommand({
        ConnectionId: connectionId,
        Data: payload,
      }));
    } catch (error) {
      if (error.statusCode === 410) {
        // Connection stale, remove from DynamoDB
        await docClient.send(new DeleteCommand({
          TableName: tableName,
          Key: { connectionId },
        }));
      } else {
        console.error(`Failed to send to ${connectionId}:`, error);
      }
    }
  }));

  return { statusCode: 200, body: `Broadcast ${messages.length} events to ${connections.length} connections` };
};
```

**Step 5: Create package.json for Lambda layer**

Create `data-stack/consolidated-data-stack/lambda/websocket/package.json`:
```json
{
  "name": "websocket-handlers",
  "version": "1.0.0",
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.500.0",
    "@aws-sdk/lib-dynamodb": "^3.500.0",
    "@aws-sdk/client-apigatewaymanagementapi": "^3.500.0"
  }
}
```

**Step 6: Commit**

```bash
git add data-stack/consolidated-data-stack/lambda/websocket/ data-stack/consolidated-data-stack/lambda/consumer/
git commit -m "feat: add WebSocket and MSK consumer Lambda handlers"
```

---

## Task 8: Create Dashboard Stack

**Files:**
- Create: `data-stack/consolidated-data-stack/lib/stacks/dashboard-stack.ts`
- Reference: `data-stack/ibc2025-data-gen-acme-video-telemetry-dashboard/telemetry-dashboard-cdk/lib/`

**Step 1: Create dashboard stack**

Create `data-stack/consolidated-data-stack/lib/stacks/dashboard-stack.ts`:
```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as apigwv2Integrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as msk from 'aws-cdk-lib/aws-msk';
import { Construct } from 'constructs';
import { Config } from '../config';
import * as path from 'path';

export interface DashboardStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  mskCluster: msk.CfnCluster;
  mskSecurityGroup: ec2.SecurityGroup;
}

export class DashboardStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DashboardStackProps) {
    super(scope, id, props);

    // DynamoDB table for WebSocket connections
    const connectionsTable = new dynamodb.Table(this, 'ConnectionsTable', {
      tableName: `${Config.prefix}-connections`,
      partitionKey: { name: 'connectionId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl',
    });

    // Lambda layer for AWS SDK
    const sdkLayer = new lambda.LayerVersion(this, 'AwsSdkLayer', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/websocket'), {
        bundling: {
          image: lambda.Runtime.NODEJS_18_X.bundlingImage,
          command: [
            'bash', '-c',
            'npm install && mkdir -p /asset-output/nodejs && cp -r node_modules /asset-output/nodejs/',
          ],
        },
      }),
      compatibleRuntimes: [lambda.Runtime.NODEJS_18_X],
      description: 'AWS SDK v3 for WebSocket handlers',
    });

    // Connect handler
    const connectFn = new lambda.Function(this, 'ConnectFunction', {
      functionName: `${Config.prefix}-ws-connect`,
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'connect.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/websocket')),
      layers: [sdkLayer],
      environment: {
        CONNECTIONS_TABLE: connectionsTable.tableName,
      },
    });
    connectionsTable.grantWriteData(connectFn);

    // Disconnect handler
    const disconnectFn = new lambda.Function(this, 'DisconnectFunction', {
      functionName: `${Config.prefix}-ws-disconnect`,
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'disconnect.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/websocket')),
      layers: [sdkLayer],
      environment: {
        CONNECTIONS_TABLE: connectionsTable.tableName,
      },
    });
    connectionsTable.grantWriteData(disconnectFn);

    // Default handler
    const defaultFn = new lambda.Function(this, 'DefaultFunction', {
      functionName: `${Config.prefix}-ws-default`,
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'default.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/websocket')),
    });

    // WebSocket API
    const webSocketApi = new apigwv2.WebSocketApi(this, 'WebSocketApi', {
      apiName: `${Config.prefix}-websocket`,
      connectRouteOptions: {
        integration: new apigwv2Integrations.WebSocketLambdaIntegration('ConnectIntegration', connectFn),
      },
      disconnectRouteOptions: {
        integration: new apigwv2Integrations.WebSocketLambdaIntegration('DisconnectIntegration', disconnectFn),
      },
      defaultRouteOptions: {
        integration: new apigwv2Integrations.WebSocketLambdaIntegration('DefaultIntegration', defaultFn),
      },
    });

    const stage = new apigwv2.WebSocketStage(this, 'WebSocketStage', {
      webSocketApi,
      stageName: 'prod',
      autoDeploy: true,
    });

    // MSK Consumer Lambda
    const consumerSg = new ec2.SecurityGroup(this, 'ConsumerSecurityGroup', {
      vpc: props.vpc,
      description: 'Security group for MSK consumer Lambda',
      allowAllOutbound: true,
    });

    props.mskSecurityGroup.addIngressRule(
      consumerSg,
      ec2.Port.tcp(9098),
      'Allow consumer Lambda to connect to MSK'
    );

    const consumerRole = new iam.Role(this, 'ConsumerRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
      ],
    });

    consumerRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'kafka:DescribeCluster',
        'kafka:GetBootstrapBrokers',
        'kafka-cluster:Connect',
        'kafka-cluster:ReadData',
        'kafka-cluster:DescribeTopic',
        'kafka-cluster:DescribeGroup',
      ],
      resources: ['*'],
    }));

    // Grant WebSocket management permissions
    consumerRole.addToPolicy(new iam.PolicyStatement({
      actions: ['execute-api:ManageConnections'],
      resources: [`arn:aws:execute-api:${this.region}:${this.account}:${webSocketApi.apiId}/*`],
    }));

    const consumerFn = new lambda.Function(this, 'ConsumerFunction', {
      functionName: `${Config.prefix}-msk-consumer`,
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/consumer')),
      layers: [sdkLayer],
      role: consumerRole,
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [consumerSg],
      timeout: cdk.Duration.minutes(5),
      memorySize: Config.lambda.consumerMemory,
      environment: {
        CONNECTIONS_TABLE: connectionsTable.tableName,
        WEBSOCKET_ENDPOINT: stage.callbackUrl,
      },
    });
    connectionsTable.grantReadWriteData(consumerFn);

    // MSK event source (requires cluster to be available)
    consumerFn.addEventSource(new lambdaEventSources.ManagedKafkaEventSource({
      clusterArn: props.mskCluster.attrArn,
      topic: Config.msk.topics.telemetry,
      batchSize: 100,
      startingPosition: lambda.StartingPosition.LATEST,
    }));

    // Outputs
    new cdk.CfnOutput(this, 'WebSocketApiEndpoint', { value: stage.url });
    new cdk.CfnOutput(this, 'ConnectionsTableName', { value: connectionsTable.tableName });
  }
}
```

**Step 2: Verify TypeScript compiles**

```bash
cd data-stack/consolidated-data-stack && npm run build
```

**Step 3: Commit**

```bash
git add data-stack/consolidated-data-stack/lib/stacks/dashboard-stack.ts
git commit -m "feat: add dashboard stack with WebSocket API and MSK consumer"
```

---

## Task 9: Test CDK Synthesis

**Files:**
- None (testing only)

**Step 1: Run CDK synth**

```bash
cd data-stack/consolidated-data-stack && npx cdk synth
```

Expected: CloudFormation templates generated for all 5 stacks in `cdk.out/`

**Step 2: Review generated templates**

```bash
ls -la cdk.out/*.template.json
```

Expected: 5 template files (Network, MSK, DataLake, DataGen, Dashboard)

**Step 3: Commit any fixes**

If synth fails, fix issues and commit:
```bash
git add -A && git commit -m "fix: resolve CDK synthesis issues"
```

---

## Task 10: Deploy to AWS

**Files:**
- None (deployment only)

**Step 1: Bootstrap CDK (if not already done)**

```bash
cd data-stack/consolidated-data-stack && npx cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/us-west-2
```

**Step 2: Deploy all stacks**

```bash
cd data-stack/consolidated-data-stack && npx cdk deploy --all --require-approval never
```

Expected: All 5 stacks deploy successfully with outputs showing:
- VPC ID
- MSK Cluster ARN
- Bootstrap Servers
- S3 Bucket Name
- WebSocket Endpoint

**Step 3: Verify resources**

```bash
# Check MSK cluster
aws kafka list-clusters --region us-west-2

# Check S3 bucket
aws s3 ls | grep acme-telemetry

# Check Lambda functions
aws lambda list-functions --region us-west-2 | grep acme-data
```

**Step 4: Commit deployment verification**

```bash
git add -A && git commit -m "chore: verified consolidated data stack deployment"
```

---

## Task 11: Create README

**Files:**
- Create: `data-stack/consolidated-data-stack/README.md`

**Step 1: Create README**

Create `data-stack/consolidated-data-stack/README.md`:
```markdown
# Consolidated Data Stack

Single CDK stack combining all ACME telemetry data infrastructure:
- MSK Kafka cluster
- Lambda data generators
- Kinesis Firehose to S3
- Glue catalog and Athena
- Real-time WebSocket dashboard

## Architecture

```
NetworkStack (VPC, Security Groups)
       ↓
MskStack (Kafka 3.5.1, 3 brokers)
       ↓
    ┌──┴──┐
    ↓     ↓
DataGenStack              DashboardStack
├─ Generator Lambda       ├─ WebSocket API
├─ Producer Lambda        ├─ Consumer Lambda
└─ Firehose → S3         └─ DynamoDB connections
       ↓
DataLakeStack
├─ S3 (telemetry data)
└─ Glue (acme_telemetry.streaming_events)
```

## Deploy

```bash
npm install
npx cdk deploy --all
```

## Destroy

```bash
npx cdk destroy --all
```

## Outputs

| Stack | Output | Description |
|-------|--------|-------------|
| Network | VpcId | VPC for all resources |
| MSK | ClusterArn | Kafka cluster ARN |
| MSK | BootstrapServers | Kafka connection string |
| DataLake | DataBucketName | S3 bucket for telemetry |
| DataLake | GlueDatabaseName | Athena database |
| Dashboard | WebSocketApiEndpoint | Real-time data endpoint |

## Query Data

```sql
SELECT event_type, COUNT(*) as count
FROM acme_telemetry.streaming_events
WHERE year = '2026' AND month = '01'
GROUP BY event_type;
```
```

**Step 2: Commit**

```bash
git add data-stack/consolidated-data-stack/README.md
git commit -m "docs: add README for consolidated data stack"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Initialize CDK project | package.json, tsconfig, cdk.json, config.ts, app.ts |
| 2 | Network stack | network-stack.ts |
| 3 | MSK stack | msk-stack.ts |
| 4 | Data lake stack | data-lake-stack.ts |
| 5 | Generator/Producer Lambdas | lambda/generator/, lambda/producer/ |
| 6 | Data generation stack | data-gen-stack.ts |
| 7 | WebSocket/Consumer Lambdas | lambda/websocket/, lambda/consumer/ |
| 8 | Dashboard stack | dashboard-stack.ts |
| 9 | Test synthesis | - |
| 10 | Deploy to AWS | - |
| 11 | Documentation | README.md |

**Total estimated commits:** 11
