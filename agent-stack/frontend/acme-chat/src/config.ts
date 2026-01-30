// Configuration for ACME Corp AgentCore Chat Application
export const config = {
  // AWS Cognito Configuration
  cognito: {
    userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID || 'us-west-2_DpzNMARcv',
    appClientId: process.env.REACT_APP_COGNITO_APP_CLIENT_ID || '7vvt961c56raslq3aeun8emf8l',
    domain: process.env.REACT_APP_COGNITO_DOMAIN || 'acme-agentcore.auth.us-west-2.amazoncognito.com',
    region: process.env.REACT_APP_AWS_REGION || 'us-west-2',
    redirectUri: process.env.REACT_APP_REDIRECT_URI || `${window.location.origin}/callback`,
    logoutUri: process.env.REACT_APP_LOGOUT_URI || window.location.origin,
  },

  // AgentCore Configuration
  agentcore: {
    agentArn: process.env.REACT_APP_AGENTCORE_ARN || 'arn:aws:bedrock-agentcore:us-west-2:878687028155:runtime/acme_chatbot-LZ92J48N6z',
    region: process.env.REACT_APP_AWS_REGION || 'us-west-2',
    endpoint: `https://bedrock-agentcore.${process.env.REACT_APP_AWS_REGION || 'us-west-2'}.amazonaws.com`
  },

  // External URLs
  external: {
    mcpRegistryUrl: process.env.REACT_APP_MCP_REGISTRY_URL || 'https://d2fyngzrxjpjlb.cloudfront.net',
    telemetryDashboardUrl: process.env.REACT_APP_TELEMETRY_DASHBOARD_URL || 'https://d22um2piuwyb63.cloudfront.net'
  }
};
