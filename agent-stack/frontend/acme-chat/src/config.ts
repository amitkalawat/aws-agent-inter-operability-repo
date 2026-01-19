// Configuration for ACME Corp AgentCore Chat Application
export const config = {
  // AWS Cognito Configuration
  cognito: {
    userPoolId: 'eu-central-1_CF2vh6s7M',
    appClientId: '3cbhcr57gvuh4ffnv6sqlha5eo',
    region: 'eu-central-1',
    discoveryUrl: 'https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_CF2vh6s7M/.well-known/openid-configuration'
  },
  
  // AgentCore Configuration
  agentcore: {
    agentArn: 'arn:aws:bedrock-agentcore:eu-central-1:241533163649:runtime/acme_chatbot_v2-rHZRzmFJCM',
    region: 'eu-central-1',
    endpoint: 'https://bedrock-agentcore.eu-central-1.amazonaws.com'
  },
  
  // Demo User Credentials (for testing)
  demo: {
    username: 'admin@acmecorp.com',
    password: 'Admin@123456!'
  },
  
  // Additional User Credentials
  demo2: {
    username: 'admin2@acmecorp.com',
    password: 'AdminPassword123!'
  },
  
  // Username mappings for simple login
  userMappings: {
    'admin': 'admin2@acmecorp.com',
    'admin1': 'admin@acmecorp.com'
  } as Record<string, string>
};