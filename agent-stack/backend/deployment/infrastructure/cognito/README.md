# Cognito Authentication for AgentCore

This directory contains scripts to set up Amazon Cognito authentication for the AgentCore chatbot.

## Overview

Amazon Cognito provides user authentication and authorization for the AgentCore deployment. This setup creates:
- **User Pool**: For user management and authentication
- **App Client**: For React application integration
- **Admin User**: Ready-to-use test account
- **JWT Tokens**: For AgentCore authorization

## Files

- `setup_cognito.py` - Creates Cognito User Pool and admin user
- `test_cognito_auth.py` - Tests authentication and token generation
- `requirements.txt` - Python dependencies
- `cognito_config.json` - Generated configuration (after setup)

## Setup Instructions

### 1. Install Dependencies

```bash
cd infrastructure/cognito
pip install -r requirements.txt
```

### 2. Run Cognito Setup

```bash
export AWS_DEFAULT_REGION=eu-central-1
python setup_cognito.py
```

**What this creates:**
- Cognito User Pool in Frankfurt region
- App Client for public React application
- Admin user with email: `admin@acmecorp.com`
- Password policy: 8+ chars, uppercase, lowercase, numbers, symbols

### 3. Test Authentication

```bash
python test_cognito_auth.py
```

**What this tests:**
- User authentication with admin credentials
- JWT token generation and validation
- Token refresh functionality
- AgentCore integration format

### 4. Review Configuration

Check `cognito_config.json` for:
```json
{
  "user_pool_id": "eu-central-1_xxxxx",
  "app_client_id": "xxxxx", 
  "region": "eu-central-1",
  "discovery_url": "https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_xxxxx/.well-known/openid-configuration",
  "admin_user": {
    "username": "admin@acmecorp.com",
    "password": "Admin@123456!"
  }
}
```

## Admin User Credentials

**Default Admin User:**
- **Username**: `admin@acmecorp.com`
- **Password**: `Admin@123456!`
- **Email Verified**: Yes
- **Status**: Active

> ⚠️ **Security Note**: Change the admin password after first login or create additional users via AWS Console.

## User Pool Configuration

### Password Policy
- Minimum 8 characters
- Requires uppercase letters
- Requires lowercase letters  
- Requires numbers
- Requires symbols

### Token Validity
- **ID Token**: 24 hours
- **Access Token**: 24 hours
- **Refresh Token**: 30 days

### Authentication Methods
- Email as username
- Email verification required
- Password authentication enabled
- SRP authentication enabled
- Refresh tokens enabled

## Creating Additional Users

### Via AWS Console
1. Go to Amazon Cognito in AWS Console
2. Select your User Pool
3. Click "Create user"
4. Enter email and temporary password
5. User will be prompted to change password on first login

### Via CLI
```bash
aws cognito-idp admin-create-user \
  --user-pool-id eu-central-1_xxxxx \
  --username newuser@acmecorp.com \
  --user-attributes Name=email,Value=newuser@acmecorp.com Name=email_verified,Value=true \
  --temporary-password TempPass@123! \
  --message-action SUPPRESS
```

## Integration with AgentCore

After Cognito setup, the configuration will be used to:

1. **Configure AgentCore Runtime** with JWT authorizer:
```python
authorizer_configuration={
    "customJWTAuthorizer": {
        "discoveryUrl": "https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_xxxxx/.well-known/openid-configuration",
        "allowedClients": ["app_client_id"]
    }
}
```

2. **Authenticate and invoke** AgentCore:
```python
# Get token from Cognito
bearer_token = authenticate_user()

# Invoke AgentCore with token
client.invoke_agent_runtime(
    agentRuntimeArn="arn:aws:bedrock-agentcore:...",
    authorizationToken=f"Bearer {bearer_token}"
)
```

## Troubleshooting

### Setup Issues
- **AWS Credentials**: Ensure AWS CLI is configured
- **Region**: Make sure using eu-central-1
- **Permissions**: Need Cognito admin permissions

### Authentication Issues
- **Wrong Password**: Use `Admin@123456!` for admin user
- **Token Expired**: Tokens expire after 24 hours
- **User Not Found**: Check username (should be email)

### Common Errors
```bash
# User pool not found
aws cognito-idp describe-user-pool --user-pool-id eu-central-1_xxxxx

# List user pools
aws cognito-idp list-user-pools --max-results 10

# Get user info
aws cognito-idp admin-get-user --user-pool-id eu-central-1_xxxxx --username admin@acmecorp.com
```

## Cleanup

To remove Cognito resources:
```bash
# Delete user pool (this deletes all users and app clients)
aws cognito-idp delete-user-pool --user-pool-id eu-central-1_xxxxx

# Remove local config
rm cognito_config.json
```

## Next Steps

After successful Cognito setup:
1. Deploy AgentCore with authentication
2. Create React frontend with Cognito integration
3. Test end-to-end authenticated flow

## Security Best Practices

- Change admin password after setup
- Use temporary passwords for new users
- Enable MFA for production users
- Monitor authentication logs
- Regularly rotate refresh tokens
- Use HTTPS only for token transmission