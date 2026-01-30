#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { Config } from '../lib/config';
import { NetworkStack } from '../lib/stacks/network-stack';
import { KinesisStack } from '../lib/stacks/kinesis-stack';
import { DataGenStack } from '../lib/stacks/data-gen-stack';
import { DataLakeStack } from '../lib/stacks/data-lake-stack';

const app = new cdk.App();

const networkStack = new NetworkStack(app, 'AcmeNetworkStack', {
  env: Config.env,
});

const kinesisStack = new KinesisStack(app, 'AcmeKinesisStack', {
  env: Config.env,
});

const dataLakeStack = new DataLakeStack(app, 'AcmeDataLakeStack', {
  env: Config.env,
});

const dataGenStack = new DataGenStack(app, 'AcmeDataGenStack', {
  env: Config.env,
  kinesisStream: kinesisStack.stream,
  dataBucket: dataLakeStack.dataBucket,
});
dataGenStack.addDependency(kinesisStack);
dataGenStack.addDependency(dataLakeStack);

app.synth();
