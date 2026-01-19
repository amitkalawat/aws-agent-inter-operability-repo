import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserPool,
  CognitoUserSession,
} from 'amazon-cognito-identity-js';
import { config } from '../config';

export interface User {
  username: string;
  email: string;
  accessToken: string;
  idToken: string;
}

class AuthService {
  private userPool: CognitoUserPool;

  /**
   * Map simple usernames to email addresses
   */
  private mapUsername(username: string): string {
    // Use centralized mappings from config
    const mappings: Record<string, string> = config.userMappings || {};
    
    // Return mapped username or original if no mapping exists
    return mappings[username.toLowerCase()] || username;
  }

  /**
   * Reverse map email addresses to display names for UI
   */
  private reverseMapUsername(email: string): string {
    const mappings: Record<string, string> = config.userMappings || {};
    
    // Find the key that maps to this email
    for (const [displayName, mappedEmail] of Object.entries(mappings)) {
      if (mappedEmail.toLowerCase() === email.toLowerCase()) {
        return displayName;
      }
    }
    
    // Return original email if no reverse mapping found
    return email;
  }

  constructor() {
    this.userPool = new CognitoUserPool({
      UserPoolId: config.cognito.userPoolId,
      ClientId: config.cognito.appClientId,
    });
  }

  /**
   * Sign in user with username and password
   */
  signIn(username: string, password: string): Promise<User> {
    return new Promise((resolve, reject) => {
      // Map username to email if needed
      const mappedUsername = this.mapUsername(username);
      
      const authenticationDetails = new AuthenticationDetails({
        Username: mappedUsername,
        Password: password,
      });

      const cognitoUser = new CognitoUser({
        Username: mappedUsername,
        Pool: this.userPool,
      });

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session: CognitoUserSession) => {
          const accessToken = session.getAccessToken().getJwtToken();
          const idToken = session.getIdToken().getJwtToken();
          
          // Extract email from ID token
          const idTokenPayload = session.getIdToken().payload;
          const email = idTokenPayload.email || username;

          const user: User = {
            username: this.reverseMapUsername(mappedUsername),
            email,
            accessToken,
            idToken,
          };

          resolve(user);
        },
        onFailure: (error) => {
          reject(new Error(error.message || 'Authentication failed'));
        },
        mfaRequired: () => {
          reject(new Error('MFA is required but not supported in this demo'));
        },
        newPasswordRequired: () => {
          reject(new Error('New password required but not supported in this demo'));
        },
      });
    });
  }

  /**
   * Sign out current user
   */
  signOut(): Promise<void> {
    return new Promise((resolve) => {
      const cognitoUser = this.userPool.getCurrentUser();
      if (cognitoUser) {
        cognitoUser.signOut();
      }
      resolve();
    });
  }

  /**
   * Get current user session
   */
  getCurrentUser(): Promise<User | null> {
    return new Promise((resolve, reject) => {
      const cognitoUser = this.userPool.getCurrentUser();
      
      if (!cognitoUser) {
        resolve(null);
        return;
      }

      cognitoUser.getSession((error: Error | null, session: CognitoUserSession | null) => {
        if (error) {
          reject(error);
          return;
        }

        if (!session || !session.isValid()) {
          resolve(null);
          return;
        }

        const accessToken = session.getAccessToken().getJwtToken();
        const idToken = session.getIdToken().getJwtToken();
        const idTokenPayload = session.getIdToken().payload;
        
        const user: User = {
          username: this.reverseMapUsername(cognitoUser.getUsername()),
          email: idTokenPayload.email || cognitoUser.getUsername(),
          accessToken,
          idToken,
        };

        resolve(user);
      });
    });
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): Promise<boolean> {
    return this.getCurrentUser()
      .then(user => user !== null)
      .catch(() => false);
  }
}

export default new AuthService();