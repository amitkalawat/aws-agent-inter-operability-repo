// Configuration for ACME Corp AgentCore Chat Application
// NOTE: Replace placeholder values with your actual AWS resource IDs after deployment
export const config = {
  // AWS Cognito Configuration
  cognito: {
    userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID || '<YOUR_COGNITO_USER_POOL_ID>',
    appClientId: process.env.REACT_APP_COGNITO_APP_CLIENT_ID || '<YOUR_COGNITO_APP_CLIENT_ID>',
    region: process.env.REACT_APP_AWS_REGION || 'us-west-2',
    discoveryUrl: `https://cognito-idp.${process.env.REACT_APP_AWS_REGION || 'us-west-2'}.amazonaws.com/${process.env.REACT_APP_COGNITO_USER_POOL_ID || '<YOUR_COGNITO_USER_POOL_ID>'}/.well-known/openid-configuration`
  },

  // AgentCore Configuration
  agentcore: {
    agentArn: process.env.REACT_APP_AGENTCORE_ARN || '<YOUR_AGENTCORE_ARN>',
    region: process.env.REACT_APP_AWS_REGION || 'us-west-2',
    endpoint: `https://bedrock-agentcore.${process.env.REACT_APP_AWS_REGION || 'us-west-2'}.amazonaws.com`
  },

  // Demo User Credentials (for testing only - use environment variables in production)
  demo: {
    username: process.env.REACT_APP_DEMO_USERNAME || 'admin@acme.com',
    password: process.env.REACT_APP_DEMO_PASSWORD || '<SET_DEMO_PASSWORD>'
  },

  // Username mappings for simple login
  userMappings: {
    'admin': 'admin@acme.com'
  } as Record<string, string>
};