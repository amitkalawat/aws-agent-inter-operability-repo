#!/usr/bin/env python3
"""
Setup Amazon Cognito User Pool for AgentCore Authentication
"""

import boto3
import json
import time
from botocore.exceptions import ClientError


def create_user_pool(cognito_client, pool_name="acme-corp-agentcore-users"):
    """Create Cognito User Pool"""
    print(f"Creating Cognito User Pool: {pool_name}")
    
    try:
        response = cognito_client.create_user_pool(
            PoolName=pool_name,
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': True,
                    'TemporaryPasswordValidityDays': 7
                }
            },
            LambdaConfig={},
            AutoVerifiedAttributes=['email'],
            UsernameAttributes=['email'],
            SmsVerificationMessage='Your verification code is {####}',
            EmailVerificationMessage='Your verification code is {####}',
            EmailVerificationSubject='ACME Corp - Verification Code',
            VerificationMessageTemplate={
                'SmsMessage': 'Your verification code is {####}',
                'EmailMessage': 'Your verification code is {####}',
                'EmailSubject': 'ACME Corp - Verification Code',
                'DefaultEmailOption': 'CONFIRM_WITH_CODE'
            },
            MfaConfiguration='OFF',
            DeviceConfiguration={
                'ChallengeRequiredOnNewDevice': False,
                'DeviceOnlyRememberedOnUserPrompt': False
            },
            EmailConfiguration={
                'EmailSendingAccount': 'COGNITO_DEFAULT'
            },
            AdminCreateUserConfig={
                'AllowAdminCreateUserOnly': False,
                'InviteMessageTemplate': {
                    'SMSMessage': 'Your username is {username} and temporary password is {####}',
                    'EmailMessage': 'Your username is {username} and temporary password is {####}',
                    'EmailSubject': 'ACME Corp - Your temporary password'
                }
            },
            UserPoolTags={
                'Project': 'ACME-Corp-AgentCore',
                'Environment': 'Development'
            },
            AccountRecoverySetting={
                'RecoveryMechanisms': [
                    {
                        'Priority': 1,
                        'Name': 'verified_email'
                    }
                ]
            }
        )
        
        user_pool_id = response['UserPool']['Id']
        print(f"✅ User Pool created: {user_pool_id}")
        return user_pool_id
        
    except ClientError as e:
        print(f"❌ Error creating user pool: {e}")
        raise


def create_user_pool_client(cognito_client, user_pool_id, client_name="acme-corp-react-app"):
    """Create User Pool App Client for React application"""
    print(f"Creating User Pool App Client: {client_name}")
    
    try:
        response = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=client_name,
            GenerateSecret=False,  # Public client for React app
            RefreshTokenValidity=30,  # 30 days
            AccessTokenValidity=24,   # 24 hours
            IdTokenValidity=24,       # 24 hours
            TokenValidityUnits={
                'AccessToken': 'hours',
                'IdToken': 'hours',
                'RefreshToken': 'days'
            },
            ReadAttributes=[
                'email',
                'email_verified',
                'name',
                'family_name',
                'given_name'
            ],
            WriteAttributes=[
                'email',
                'name',
                'family_name', 
                'given_name'
            ],
            ExplicitAuthFlows=[
                'ALLOW_USER_SRP_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH',
                'ALLOW_USER_PASSWORD_AUTH'  # For testing and admin access
            ],
            PreventUserExistenceErrors='ENABLED',
            EnableTokenRevocation=True
        )
        
        app_client_id = response['UserPoolClient']['ClientId']
        print(f"✅ App Client created: {app_client_id}")
        return app_client_id
        
    except ClientError as e:
        print(f"❌ Error creating app client: {e}")
        raise


def create_admin_user(cognito_client, user_pool_id, username=None, temp_password=None):
    """Create admin user"""
    print(f"Creating admin user: {username}")
    
    try:
        # Create user
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': username
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'name',
                    'Value': 'ACME Admin'
                },
                {
                    'Name': 'given_name',
                    'Value': 'ACME'
                },
                {
                    'Name': 'family_name',
                    'Value': 'Admin'
                }
            ],
            TemporaryPassword=temp_password,
            MessageAction='SUPPRESS'  # Don't send welcome email
        )
        
        print(f"✅ Admin user created: {username}")
        
        # Set permanent password - REPLACE WITH YOUR SECURE PASSWORD
        permanent_password = os.environ.get('COGNITO_ADMIN_PASSWORD', '<SET_SECURE_PASSWORD>')
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=permanent_password,
            Permanent=True
        )
        
        print(f"✅ Permanent password set for admin user")
        print(f"   Username: {username}")
        print(f"   Password: {permanent_password}")
        
        return username, permanent_password
        
    except ClientError as e:
        print(f"❌ Error creating admin user: {e}")
        raise


def get_discovery_url(region, user_pool_id):
    """Generate OpenID Connect discovery URL"""
    discovery_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    return discovery_url


def save_config(config, filename="cognito_config.json"):
    """Save configuration to file"""
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Configuration saved to {filename}")


def main():
    """Main setup function"""
    print("=== ACME Corp Cognito Setup for AgentCore ===")
    
    # Initialize Cognito client
    session = boto3.Session()
    region = session.region_name or 'eu-central-1'
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    print(f"Using AWS region: {region}")
    
    try:
        # Create User Pool
        user_pool_id = create_user_pool(cognito_client)
        
        # Create App Client
        app_client_id = create_user_pool_client(cognito_client, user_pool_id)
        
        # Create admin user
        admin_username, admin_password = create_admin_user(cognito_client, user_pool_id)
        
        # Generate discovery URL
        discovery_url = get_discovery_url(region, user_pool_id)
        
        # Prepare configuration
        config = {
            "user_pool_id": user_pool_id,
            "app_client_id": app_client_id,
            "region": region,
            "discovery_url": discovery_url,
            "admin_user": {
                "username": admin_username,
                "password": admin_password
            },
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "notes": "Created for ACME Corp AgentCore authentication"
        }
        
        # Save configuration
        save_config(config)
        
        print("\n=== Setup Complete ===")
        print(f"✅ User Pool ID: {user_pool_id}")
        print(f"✅ App Client ID: {app_client_id}")
        print(f"✅ Discovery URL: {discovery_url}")
        print(f"✅ Admin User: {admin_username}")
        print(f"✅ Admin Password: {admin_password}")
        print(f"✅ Configuration saved to: cognito_config.json")
        
        print("\n=== Next Steps ===")
        print("1. Test authentication with: python test_cognito_auth.py")
        print("2. Deploy AgentCore with authentication")
        print("3. Create additional users via AWS Console if needed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)