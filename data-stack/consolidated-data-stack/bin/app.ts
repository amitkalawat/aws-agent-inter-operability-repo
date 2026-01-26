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
  lambdaSecurityGroup: networkStack.lambdaSecurityGroup,
  dataBucket: dataLakeStack.dataBucket,
});
dataGenStack.addDependency(mskStack);
dataGenStack.addDependency(dataLakeStack);

const dashboardStack = new DashboardStack(app, 'AcmeDashboardStack', {
  env: Config.env,
  vpc: networkStack.vpc,
  mskCluster: mskStack.cluster,
  lambdaSecurityGroup: networkStack.lambdaSecurityGroup,
});
dashboardStack.addDependency(mskStack);

app.synth();
