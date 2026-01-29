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

class AuthServiceClass {
  private userPool: CognitoUserPool;

  constructor() {
    this.userPool = new CognitoUserPool({
      UserPoolId: config.cognito.userPoolId,
      ClientId: config.cognito.appClientId,
    });
  }

  signIn(email: string, password: string): Promise<User> {
    return new Promise((resolve, reject) => {
      const authenticationDetails = new AuthenticationDetails({
        Username: email,
        Password: password,
      });

      const cognitoUser = new CognitoUser({
        Username: email,
        Pool: this.userPool,
      });

      cognitoUser.setAuthenticationFlowType('USER_PASSWORD_AUTH');

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session: CognitoUserSession) => {
          const accessToken = session.getAccessToken().getJwtToken();
          const idToken = session.getIdToken().getJwtToken();
          const idTokenPayload = session.getIdToken().payload;

          const user: User = {
            username: idTokenPayload.email || email,
            email: idTokenPayload.email || email,
            accessToken,
            idToken,
          };

          resolve(user);
        },
        onFailure: (error) => {
          reject(new Error(error.message || 'Authentication failed'));
        },
        newPasswordRequired: () => {
          reject(new Error('Password change required. Please contact administrator.'));
        },
      });
    });
  }

  signOut(): Promise<void> {
    return new Promise((resolve) => {
      const cognitoUser = this.userPool.getCurrentUser();
      if (cognitoUser) {
        cognitoUser.signOut();
      }
      resolve();
    });
  }

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
          username: cognitoUser.getUsername(),
          email: idTokenPayload.email || cognitoUser.getUsername(),
          accessToken,
          idToken,
        };

        resolve(user);
      });
    });
  }

  getAccessToken(): Promise<string> {
    return new Promise((resolve, reject) => {
      const cognitoUser = this.userPool.getCurrentUser();

      if (!cognitoUser) {
        reject(new Error('No user logged in'));
        return;
      }

      cognitoUser.getSession((error: Error | null, session: CognitoUserSession | null) => {
        if (error || !session) {
          reject(new Error('Failed to get session'));
          return;
        }

        // Use ID token for API Gateway Cognito authorizer
        resolve(session.getIdToken().getJwtToken());
      });
    });
  }

  isAuthenticated(): Promise<boolean> {
    return this.getCurrentUser()
      .then((user) => user !== null)
      .catch(() => false);
  }
}

export const AuthService = new AuthServiceClass();
