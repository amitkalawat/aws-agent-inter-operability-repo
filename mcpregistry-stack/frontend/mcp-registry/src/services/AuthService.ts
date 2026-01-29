import { config } from '../config';

export interface User {
  username: string;
  email: string;
  accessToken: string;
  idToken: string;
}

interface TokenResponse {
  access_token: string;
  id_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
}

// PKCE helper functions
function generateRandomString(length: number): string {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
  const randomValues = new Uint8Array(length);
  crypto.getRandomValues(randomValues);
  return Array.from(randomValues, (v) => charset[v % charset.length]).join('');
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function parseJwt(token: string): Record<string, unknown> {
  const base64Url = token.split('.')[1];
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const jsonPayload = decodeURIComponent(
    atob(base64)
      .split('')
      .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
      .join('')
  );
  return JSON.parse(jsonPayload);
}

class AuthServiceClass {
  private readonly TOKEN_KEY = 'mcp_registry_tokens';
  private readonly VERIFIER_KEY = 'mcp_registry_code_verifier';

  // Redirect to Cognito hosted UI for login
  async login(): Promise<void> {
    const codeVerifier = generateRandomString(64);
    const codeChallenge = await generateCodeChallenge(codeVerifier);

    // Store verifier for token exchange
    sessionStorage.setItem(this.VERIFIER_KEY, codeVerifier);

    const params = new URLSearchParams({
      client_id: config.cognito.appClientId,
      response_type: 'code',
      scope: 'openid email profile',
      redirect_uri: config.cognito.redirectUri,
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
    });

    const loginUrl = `https://${config.cognito.domain}/oauth2/authorize?${params.toString()}`;
    window.location.href = loginUrl;
  }

  // Handle OAuth callback - exchange code for tokens
  async handleCallback(code: string): Promise<User> {
    const codeVerifier = sessionStorage.getItem(this.VERIFIER_KEY);
    if (!codeVerifier) {
      throw new Error('No code verifier found. Please try logging in again.');
    }

    const tokenUrl = `https://${config.cognito.domain}/oauth2/token`;

    const params = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: config.cognito.appClientId,
      code: code,
      redirect_uri: config.cognito.redirectUri,
      code_verifier: codeVerifier,
    });

    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Token exchange failed:', error);
      throw new Error('Failed to exchange code for tokens');
    }

    const tokens: TokenResponse = await response.json();

    // Clear the verifier
    sessionStorage.removeItem(this.VERIFIER_KEY);

    // Store tokens
    this.storeTokens(tokens);

    return this.getUserFromTokens(tokens);
  }

  // Sign out - clear local tokens and redirect to Cognito logout
  async signOut(): Promise<void> {
    localStorage.removeItem(this.TOKEN_KEY);

    const params = new URLSearchParams({
      client_id: config.cognito.appClientId,
      logout_uri: config.cognito.logoutUri,
    });

    const logoutUrl = `https://${config.cognito.domain}/logout?${params.toString()}`;
    window.location.href = logoutUrl;
  }

  // Get current user from stored tokens
  async getCurrentUser(): Promise<User | null> {
    const tokens = this.getStoredTokens();
    if (!tokens) {
      return null;
    }

    // Check if token is expired
    const idTokenPayload = parseJwt(tokens.id_token);
    const exp = idTokenPayload.exp as number;
    if (Date.now() >= exp * 1000) {
      // Token expired, try to refresh
      if (tokens.refresh_token) {
        try {
          return await this.refreshTokens(tokens.refresh_token);
        } catch {
          localStorage.removeItem(this.TOKEN_KEY);
          return null;
        }
      }
      localStorage.removeItem(this.TOKEN_KEY);
      return null;
    }

    return this.getUserFromTokens(tokens);
  }

  // Get access token for API calls
  async getAccessToken(): Promise<string> {
    const user = await this.getCurrentUser();
    if (!user) {
      throw new Error('No user logged in');
    }
    return user.idToken; // Use ID token for API Gateway Cognito authorizer
  }

  // Check if user is authenticated
  async isAuthenticated(): Promise<boolean> {
    const user = await this.getCurrentUser();
    return user !== null;
  }

  // Check if this is an OAuth callback
  isCallback(): boolean {
    const params = new URLSearchParams(window.location.search);
    return params.has('code');
  }

  // Get the authorization code from URL
  getCallbackCode(): string | null {
    const params = new URLSearchParams(window.location.search);
    return params.get('code');
  }

  private async refreshTokens(refreshToken: string): Promise<User> {
    const tokenUrl = `https://${config.cognito.domain}/oauth2/token`;

    const params = new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: config.cognito.appClientId,
      refresh_token: refreshToken,
    });

    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh tokens');
    }

    const tokens: TokenResponse = await response.json();
    // Preserve refresh token if not returned
    if (!tokens.refresh_token) {
      tokens.refresh_token = refreshToken;
    }

    this.storeTokens(tokens);
    return this.getUserFromTokens(tokens);
  }

  private storeTokens(tokens: TokenResponse): void {
    localStorage.setItem(this.TOKEN_KEY, JSON.stringify(tokens));
  }

  private getStoredTokens(): TokenResponse | null {
    const stored = localStorage.getItem(this.TOKEN_KEY);
    if (!stored) {
      return null;
    }
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  }

  private getUserFromTokens(tokens: TokenResponse): User {
    const idTokenPayload = parseJwt(tokens.id_token);
    return {
      username: (idTokenPayload.email as string) || (idTokenPayload['cognito:username'] as string) || 'unknown',
      email: (idTokenPayload.email as string) || '',
      accessToken: tokens.access_token,
      idToken: tokens.id_token,
    };
  }
}

export const AuthService = new AuthServiceClass();
