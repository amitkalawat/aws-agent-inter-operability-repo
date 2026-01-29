// Configuration for MCP Registry Frontend

export const config = {
  cognito: {
    userPoolId: 'us-west-2_5j3rJtNHl',
    appClientId: '455f6cimejtaihn6g7ro9auak6',
    region: 'us-west-2',
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
