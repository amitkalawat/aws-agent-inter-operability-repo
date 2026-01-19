#!/usr/bin/env python3
"""
Deploy Strands Agent to Amazon Bedrock AgentCore with Cognito Authentication
"""

import json
import boto3
import time
import os
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session


def load_config():
    """Load configuration from config.json"""
    try:
        with open('../agent/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "agent_name": "strands_claude_getting_started_auth",
            "entrypoint": "../agent/strands_claude.py",
            "requirements_file": "../agent/requirements.txt"
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
    with open('deployment_info_auth.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    print(f"Deployment info saved to deployment_info_auth.json")


def test_deployment_with_auth(agentcore_runtime, agent_arn, cognito_config):
    """Test the deployed agent with authenticated invocations"""
    print("\n=== Testing Authenticated Agent ===")
    
    # Import here to avoid dependency issues if not available
    try:
        from warrant import Cognito
    except ImportError:
        print("❌ warrant library not found. Install with: pip install warrant")
        return False
    
    # Authenticate to get bearer token
    try:
        print("Authenticating with Cognito...")
        u = Cognito(
            cognito_config['user_pool_id'], 
            cognito_config['app_client_id'], 
            username=cognito_config['admin_user']['username']
        )
        u.authenticate(password=cognito_config['admin_user']['password'])
        bearer_token = u.id_token
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    test_cases = [
        {"prompt": "What is the weather now?"},
        {"prompt": "What is 2+2?"},
        {"prompt": "Tell me about artificial intelligence"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nAuthenticated Test {i}: {test_case['prompt']}")
        try:
            # Test with runtime invoke using bearer token
            response = agentcore_runtime.invoke(test_case, bearer_token=bearer_token)
            print(f"✅ Response: {response}")
        except Exception as e:
            print(f"❌ Error during test {i}: {e}")
    
    # Test with boto3 client
    print(f"\n=== Testing with Boto3 Client + Auth ===")
    try:
        boto_session = Session()
        region = boto_session.region_name
        agentcore_client = boto3.client('bedrock-agentcore', region_name=region)
        
        boto3_response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps({"prompt": "What is 5+3?"}),
            authorizationToken=f"Bearer {bearer_token}"
        )
        print(f"✅ Boto3 Authenticated Response: {boto3_response}")
    except Exception as e:
        print(f"❌ Boto3 authenticated test failed: {e}")
    
    return True


def main():
    """Main deployment function with authentication"""
    print("=== Amazon Bedrock AgentCore Deployment with Cognito Auth ===")
    
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
    print("\n=== Configuring Agent with Cognito Authentication ===")
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
                    "allowedClients": [cognito_config["app_client_id"]]  # Access tokens: client_id = App Client ID
                }
            }
        )
        print(f"✅ Configuration with auth successful: {response}")
    except Exception as e:
        print(f"❌ Error during configuration: {e}")
        return False
    
    # Launch the agent
    print("\n=== Launching Authenticated Agent ===")
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
        test_deployment_with_auth(agentcore_runtime, launch_result.agent_arn, cognito_config)
        
        print(f"\n=== Authenticated Deployment Complete ===")
        print(f"✅ Agent deployed successfully with Cognito authentication!")
        print(f"✅ Agent ARN: {launch_result.agent_arn}")
        print(f"✅ Authentication: Cognito JWT required")
        print(f"✅ Admin User: {cognito_config['admin_user']['username']}")
        print(f"✅ Use cleanup_agent_auth.py to clean up resources when done.")
        
        print(f"\n=== Authentication Details ===")
        print(f"🔐 User Pool ID: {cognito_config['user_pool_id']}")
        print(f"🔐 App Client ID: {cognito_config['app_client_id']}")
        print(f"🔐 Discovery URL: {cognito_config['discovery_url']}")
        print(f"🔐 Admin Username: {cognito_config['admin_user']['username']}")
        print(f"🔐 Admin Password: {cognito_config['admin_user']['password']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during launch: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)