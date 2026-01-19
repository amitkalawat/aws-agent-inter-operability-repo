// Configuration for ACME Corp AgentCore Chat Application
export const config = {
  // AWS Cognito Configuration
  cognito: {
    userPoolId: 'us-west-2_5j3rJtNHl',
    appClientId: '455f6cimejtaihn6g7ro9auak6',
    region: 'us-west-2',
    discoveryUrl: 'https://cognito-idp.us-west-2.amazonaws.com/us-west-2_5j3rJtNHl/.well-known/openid-configuration'
  },

  // AgentCore Configuration
  agentcore: {
    agentArn: 'arn:aws:bedrock-agentcore:us-west-2:878687028155:runtime/acme_chatbot-RB6voZDbJ7',
    region: 'us-west-2',
    endpoint: 'https://bedrock-agentcore.us-west-2.amazonaws.com'
  },

  // Demo User Credentials (for testing)
  demo: {
    username: 'admin@acme.com',
    password: 'Test1234!'
  },

  // Username mappings for simple login
  userMappings: {
    'admin': 'admin@acme.com'
  } as Record<string, string>
};