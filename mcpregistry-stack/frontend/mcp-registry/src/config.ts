// Configuration for MCP Registry Frontend

export const config = {
  cognito: {
    userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '<YOUR_COGNITO_USER_POOL_ID>',
    appClientId: import.meta.env.VITE_COGNITO_APP_CLIENT_ID || '<YOUR_COGNITO_APP_CLIENT_ID>',
    region: import.meta.env.VITE_AWS_REGION || 'us-west-2',
  },
  api: {
    baseUrl: '/api',
  },
};

// Amplify v6 configuration - using resourcesConfig format
export const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: config.cognito.userPoolId,
      userPoolClientId: config.cognito.appClientId,
    },
  },
};
