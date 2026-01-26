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
