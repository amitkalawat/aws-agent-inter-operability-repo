import { Construct } from 'constructs';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as cdk from 'aws-cdk-lib';

export class CognitoAuth extends Construct {
  public readonly userPool: cognito.UserPool;
  public readonly userPoolClient: cognito.UserPoolClient;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    // User Pool
    this.userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: 'telemetry-dashboard-users',
      selfSignUpEnabled: false,
      signInAliases: { username: true },
      autoVerify: { email: false },
      mfa: cognito.Mfa.OFF,
      passwordPolicy: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireDigits: true,
        requireSymbols: false,
      },
      accountRecovery: cognito.AccountRecovery.NONE,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    // App Client
    this.userPoolClient = new cognito.UserPoolClient(this, 'UserPoolClient', {
      userPool: this.userPool,
      userPoolClientName: 'telemetry-dashboard-client',
      authFlows: {
        userPassword: true,
        userSrp: true
      },
      generateSecret: false,
      preventUserExistenceErrors: true,
      accessTokenValidity: cdk.Duration.hours(1),
      idTokenValidity: cdk.Duration.hours(1),
      refreshTokenValidity: cdk.Duration.days(30)
    });
  }
}