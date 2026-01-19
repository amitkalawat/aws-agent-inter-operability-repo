#!/usr/bin/env python3
"""
Deploy Fresh ACME Chatbot Agent to Amazon Bedrock AgentCore with Cognito Authentication
"""

import json
import boto3
import time
import os
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session


def load_config():
    """Load configuration with new agent name"""
    return {
        "agent_name": "acme_chatbot_v2",
        "entrypoint": "strands_claude.py",
        "requirements_file": "requirements.txt",
        "model_id": "eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "description": "ACME Corp chatbot agent v2 with Bedrock model and Cognito authentication",
        "authentication": {
            "enabled": True,
            "type": "cognito_jwt",
            "notes": "Requires Cognito JWT access token for invocation"
        }
    }


def load_cognito_config():
    """Load Cognito configuration"""
    cognito_config_path = '../../infrastructure/cognito/cognito_config.json'
    
    if not os.path.exists(cognito_config_path):
        print(f"❌ Cognito configuration not found at {cognito_config_path}")
        print("   Run infrastructure/cognito/setup_cognito.py first")
        return None
    
    try:
        with open(cognito_config_path, 'r') as f:
            cognito_config = json.load(f)
        print(f"✅ Cognito configuration loaded")
        print(f"   User Pool ID: {cognito_config['user_pool_id']}")
        print(f"   App Client ID: {cognito_config['app_client_id']}")
        print(f"   Discovery URL: {cognito_config['discovery_url']}")
        return cognito_config
    except Exception as e:
        print(f"❌ Error loading Cognito configuration: {e}")
        return None


def save_deployment_info(deployment_info):
    """Save deployment information for cleanup"""
    with open('deployment_info_v2.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    print(f"Deployment info saved to deployment_info_v2.json")


def test_deployment_with_auth(agent_arn, cognito_config):
    """Test the deployed agent with authenticated invocations"""
    print("\n=== Testing Authenticated Agent ===")
    
    # Get access token using boto3
    try:
        print("Getting access token with boto3...")
        client = boto3.client('cognito-idp', region_name='eu-central-1')
        
        response = client.initiate_auth(
            ClientId=cognito_config['app_client_id'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': cognito_config['admin_user']['username'],
                'PASSWORD': cognito_config['admin_user']['password']
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']
        print("✅ Access token obtained")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Test with direct HTTP requests
    import requests
    
    test_cases = [
        "What is the weather now?",
        "What is 2+2?",
        "Tell me about artificial intelligence"
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\nAuthenticated Test {i}: {query}")
        try:
            # URL encode the ARN
            encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
            url = f"https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
            
            # Generate session ID
            timestamp = str(int(time.time()))
            session_id = f'test-session-{timestamp}-{i:03d}-long-enough-for-aws-requirements'
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Amzn-Trace-Id': f'trace-{timestamp}-{i}',
                'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': session_id
            }
            
            payload = {"prompt": query}
            
            print(f"Making request to: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code == 200:
                print(f"✅ Response: {response.text[:200]}...")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during test {i}: {e}")
    
    return True


def main():
    """Main deployment function with authentication"""
    print("=== Amazon Bedrock AgentCore Fresh Deployment with Cognito Auth ===")
    
    # Load configurations
    config = load_config()
    print(f"Agent configuration loaded: {config}")
    
    cognito_config = load_cognito_config()
    if not cognito_config:
        return False
    
    # Set up AWS session
    boto_session = Session()
    region = boto_session.region_name
    print(f"Using AWS region: {region}")
    
    # Initialize runtime
    print("\n=== Initializing AgentCore Runtime ===")
    agentcore_runtime = Runtime()
    
    # Configure the agent WITH authentication
    print("\n=== Configuring Fresh Agent with Cognito Authentication ===")
    try:
        response = agentcore_runtime.configure(
            entrypoint="strands_claude.py",
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region,
            agent_name=config["agent_name"],
            authorizer_configuration={
                "customJWTAuthorizer": {
                    "discoveryUrl": cognito_config["discovery_url"],
                    "allowedClients": [cognito_config["app_client_id"]]
                }
            }
        )
        print(f"✅ Configuration with auth successful: {response}")
    except Exception as e:
        print(f"❌ Error during configuration: {e}")
        return False
    
    # Launch the agent
    print("\n=== Launching Fresh Authenticated Agent ===")
    try:
        launch_result = agentcore_runtime.launch()
        print(f"✅ Launch successful!")
        print(f"Agent ID: {launch_result.agent_id}")
        print(f"ECR URI: {launch_result.ecr_uri}")
        print(f"Agent ARN: {launch_result.agent_arn}")
        
        # Save deployment information
        deployment_info = {
            "agent_id": launch_result.agent_id,
            "ecr_uri": launch_result.ecr_uri,
            "agent_arn": launch_result.agent_arn,
            "region": region,
            "agent_name": config["agent_name"],
            "deployment_timestamp": time.time(),
            "authentication": {
                "enabled": True,
                "type": "cognito_jwt",
                "user_pool_id": cognito_config["user_pool_id"],
                "app_client_id": cognito_config["app_client_id"],
                "discovery_url": cognito_config["discovery_url"]
            }
        }
        save_deployment_info(deployment_info)
        
        # Test the authenticated deployment
        test_deployment_with_auth(launch_result.agent_arn, cognito_config)
        
        print(f"\n=== Fresh Authenticated Deployment Complete ===")
        print(f"✅ Fresh agent deployed successfully with Cognito authentication!")
        print(f"✅ Agent ARN: {launch_result.agent_arn}")
        print(f"✅ Authentication: Cognito JWT required")
        print(f"✅ Admin User: {cognito_config['admin_user']['username']}")
        
        print(f"\n=== Authentication Details ===")
        print(f"🔐 User Pool ID: {cognito_config['user_pool_id']}")
        print(f"🔐 App Client ID: {cognito_config['app_client_id']}")
        print(f"🔐 Discovery URL: {cognito_config['discovery_url']}")
        print(f"🔐 Admin Username: {cognito_config['admin_user']['username']}")
        
        print(f"\n=== Next Steps ===")
        print(f"📝 Update frontend config.ts with new agent ARN:")
        print(f"   agentArn: '{launch_result.agent_arn}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during launch: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)