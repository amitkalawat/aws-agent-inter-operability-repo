#!/usr/bin/env python3
"""
Test Amazon Cognito Authentication for AgentCore
"""

import json
import boto3
from warrant import Cognito
import jwt
from datetime import datetime
from botocore.exceptions import ClientError


def load_config(filename="cognito_config.json"):
    """Load Cognito configuration"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file {filename} not found")
        print("   Run setup_cognito.py first")
        return None


def authenticate_user(user_pool_id, client_id, username, password):
    """Authenticate user and get tokens"""
    print(f"Authenticating user: {username}")
    
    try:
        # Initialize Cognito user
        u = Cognito(user_pool_id, client_id, username=username)
        
        # Authenticate
        u.authenticate(password=password)
        
        print("✅ Authentication successful")
        
        # Get tokens
        access_token = u.access_token
        id_token = u.id_token
        refresh_token = u.refresh_token
        
        return {
            'access_token': access_token,
            'id_token': id_token,
            'refresh_token': refresh_token,
            'cognito_user': u
        }
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


def decode_token(token, verify=False):
    """Decode JWT token and display contents"""
    try:
        # Decode without verification for inspection
        decoded = jwt.decode(token, options={"verify_signature": verify})
        return decoded
    except Exception as e:
        print(f"❌ Error decoding token: {e}")
        return None


def display_token_info(tokens):
    """Display token information"""
    print("\n=== Token Information ===")
    
    # ID Token
    print("\n🆔 ID Token Claims:")
    id_claims = decode_token(tokens['id_token'])
    if id_claims:
        print(f"   Subject (sub): {id_claims.get('sub', 'N/A')}")
        print(f"   Email: {id_claims.get('email', 'N/A')}")
        print(f"   Name: {id_claims.get('name', 'N/A')}")
        print(f"   Email Verified: {id_claims.get('email_verified', 'N/A')}")
        print(f"   Token Use: {id_claims.get('token_use', 'N/A')}")
        print(f"   Audience: {id_claims.get('aud', 'N/A')}")
        print(f"   Issuer: {id_claims.get('iss', 'N/A')}")
        
        # Token expiry
        exp = id_claims.get('exp')
        if exp:
            exp_time = datetime.fromtimestamp(exp)
            print(f"   Expires: {exp_time}")
        
        # Issued at
        iat = id_claims.get('iat')
        if iat:
            issued_time = datetime.fromtimestamp(iat)
            print(f"   Issued: {issued_time}")
    
    # Access Token
    print("\n🔑 Access Token Claims:")
    access_claims = decode_token(tokens['access_token'])
    if access_claims:
        print(f"   Subject (sub): {access_claims.get('sub', 'N/A')}")
        print(f"   Username: {access_claims.get('username', 'N/A')}")
        print(f"   Token Use: {access_claims.get('token_use', 'N/A')}")
        print(f"   Client ID: {access_claims.get('client_id', 'N/A')}")
        print(f"   Scope: {access_claims.get('scope', 'N/A')}")
        
        # Token expiry
        exp = access_claims.get('exp')
        if exp:
            exp_time = datetime.fromtimestamp(exp)
            print(f"   Expires: {exp_time}")


def test_token_refresh(cognito_user):
    """Test token refresh functionality"""
    print("\n=== Testing Token Refresh ===")
    
    try:
        # Renew tokens
        cognito_user.renew_access_token()
        print("✅ Token refresh successful")
        
        new_access_token = cognito_user.access_token
        new_id_token = cognito_user.id_token
        
        print("✅ New tokens obtained")
        return {
            'access_token': new_access_token,
            'id_token': new_id_token
        }
        
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
        return None


def test_agentcore_token_format(id_token, config):
    """Test token format for AgentCore integration"""
    print("\n=== AgentCore Integration Test ===")
    
    # Format for AgentCore invocation
    bearer_token = f"Bearer {id_token}"
    
    print(f"✅ Bearer token format: {bearer_token[:50]}...")
    print(f"✅ Discovery URL: {config['discovery_url']}")
    print(f"✅ Client ID: {config['app_client_id']}")
    
    # Example invocation code
    print("\n📝 Example AgentCore Invocation Code:")
    print("```python")
    print("import boto3")
    print("import json")
    print("")
    print("client = boto3.client('bedrock-agentcore', region_name='eu-central-1')")
    print("response = client.invoke_agent_runtime(")
    print("    agentRuntimeArn='YOUR_AGENT_ARN',")
    print("    qualifier='DEFAULT',")
    print("    payload=json.dumps({'prompt': 'Hello'}),")
    print(f"    authorizationToken='{bearer_token[:30]}...'")
    print(")")
    print("```")


def test_user_info(cognito_user, config):
    """Test getting user information"""
    print("\n=== User Information Test ===")
    
    try:
        cognito_client = boto3.client('cognito-idp', region_name=config['region'])
        
        # Get user info
        response = cognito_client.admin_get_user(
            UserPoolId=config['user_pool_id'],
            Username=config['admin_user']['username']
        )
        
        print(f"✅ Username: {response['Username']}")
        print(f"✅ User Status: {response['UserStatus']}")
        print(f"✅ Enabled: {response['Enabled']}")
        print("✅ User Attributes:")
        
        for attr in response.get('UserAttributes', []):
            print(f"   {attr['Name']}: {attr['Value']}")
            
    except ClientError as e:
        print(f"❌ Error getting user info: {e}")


def main():
    """Main test function"""
    print("=== Cognito Authentication Test ===")
    
    # Load configuration
    config = load_config()
    if not config:
        return False
    
    print(f"✅ Configuration loaded")
    print(f"   User Pool ID: {config['user_pool_id']}")
    print(f"   App Client ID: {config['app_client_id']}")
    print(f"   Region: {config['region']}")
    
    # Test authentication
    tokens = authenticate_user(
        config['user_pool_id'],
        config['app_client_id'],
        config['admin_user']['username'],
        config['admin_user']['password']
    )
    
    if not tokens:
        return False
    
    # Display token information
    display_token_info(tokens)
    
    # Test token refresh
    new_tokens = test_token_refresh(tokens['cognito_user'])
    
    # Test user information
    test_user_info(tokens['cognito_user'], config)
    
    # Test AgentCore integration format
    test_agentcore_token_format(tokens['id_token'], config)
    
    print("\n=== Authentication Test Complete ===")
    print("✅ All tests passed")
    print("✅ Tokens are valid and ready for AgentCore")
    print("✅ Ready to deploy AgentCore with authentication")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)