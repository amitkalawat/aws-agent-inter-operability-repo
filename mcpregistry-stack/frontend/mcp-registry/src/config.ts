// Configuration for MCP Registry Frontend

export const config = {
  cognito: {
    userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || 'us-west-2_5j3rJtNHl',
    appClientId: import.meta.env.VITE_COGNITO_APP_CLIENT_ID || '455f6cimejtaihn6g7ro9auak6',
    domain: import.meta.env.VITE_COGNITO_DOMAIN || 'acme-agentcore.auth.us-west-2.amazoncognito.com',
    region: import.meta.env.VITE_AWS_REGION || 'us-west-2',
    redirectUri: import.meta.env.VITE_REDIRECT_URI || `${window.location.origin}/callback`,
    logoutUri: import.meta.env.VITE_LOGOUT_URI || window.location.origin,
  },
  api: {
    baseUrl: '/api',
  },
};
