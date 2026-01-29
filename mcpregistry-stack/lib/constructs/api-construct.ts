import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import { Config } from '../config';

export interface ApiConstructProps {
  userPool: cognito.IUserPool;
  lambdas: {
    listServers: lambda.Function;
    getServer: lambda.Function;
    createServer: lambda.Function;
    updateServer: lambda.Function;
    deleteServer: lambda.Function;
    getTools: lambda.Function;
  };
}

export class ApiConstruct extends Construct {
  public readonly api: apigateway.RestApi;

  constructor(scope: Construct, id: string, props: ApiConstructProps) {
    super(scope, id);

    // Create REST API
    this.api = new apigateway.RestApi(this, 'McpRegistryApi', {
      restApiName: `${Config.naming.prefix}-api`,
      description: 'MCP Server Registry API',
      deployOptions: {
        stageName: Config.api.stageName,
        throttlingBurstLimit: 100,
        throttlingRateLimit: 50,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'Authorization',
          'X-Amz-Date',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
        allowCredentials: true,
      },
    });

    // Cognito authorizer
    const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'CognitoAuthorizer', {
      cognitoUserPools: [props.userPool],
      authorizerName: `${Config.naming.prefix}-authorizer`,
      identitySource: 'method.request.header.Authorization',
    });

    const authOptions: apigateway.MethodOptions = {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    };

    // API resource structure: /api/servers
    const apiResource = this.api.root.addResource('api');
    const serversResource = apiResource.addResource('servers');
    const serverIdResource = serversResource.addResource('{id}');
    const toolsResource = serverIdResource.addResource('tools');

    // Lambda integrations
    const listIntegration = new apigateway.LambdaIntegration(props.lambdas.listServers);
    const getIntegration = new apigateway.LambdaIntegration(props.lambdas.getServer);
    const createIntegration = new apigateway.LambdaIntegration(props.lambdas.createServer);
    const updateIntegration = new apigateway.LambdaIntegration(props.lambdas.updateServer);
    const deleteIntegration = new apigateway.LambdaIntegration(props.lambdas.deleteServer);
    const getToolsIntegration = new apigateway.LambdaIntegration(props.lambdas.getTools);

    // Routes
    // GET /api/servers - List servers
    serversResource.addMethod('GET', listIntegration, authOptions);

    // POST /api/servers - Create server
    serversResource.addMethod('POST', createIntegration, authOptions);

    // GET /api/servers/{id} - Get server
    serverIdResource.addMethod('GET', getIntegration, authOptions);

    // PUT /api/servers/{id} - Update server
    serverIdResource.addMethod('PUT', updateIntegration, authOptions);

    // DELETE /api/servers/{id} - Delete server
    serverIdResource.addMethod('DELETE', deleteIntegration, authOptions);

    // GET /api/servers/{id}/tools - Get/refresh tools
    toolsResource.addMethod('GET', getToolsIntegration, authOptions);

    // POST /api/servers/{id}/tools/refresh - Force refresh tools
    const refreshResource = toolsResource.addResource('refresh');
    refreshResource.addMethod('POST', getToolsIntegration, authOptions);

    // Output API URL
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.api.url,
      description: 'MCP Registry API URL',
      exportName: 'McpRegistryApiUrl',
    });
  }
}
