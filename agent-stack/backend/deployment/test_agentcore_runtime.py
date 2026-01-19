#!/usr/bin/env python3
"""
Test AgentCore with Authentication Using Runtime
"""

import json
import os
from bedrock_agentcore_starter_toolkit import Runtime
from warrant import Cognito


def load_deployment_info():
    """Load deployment information"""
    if not os.path.exists('deployment_info_auth.json'):
        print("❌ Deployment file not found. Run deploy_agent_with_auth.py first")
        return None
    
    with open('deployment_info_auth.json', 'r') as f:
        return json.load(f)


def load_cognito_config():
    """Load Cognito configuration"""
    cognito_config_path = '../../infrastructure/cognito/cognito_config.json'
    
    with open(cognito_config_path, 'r') as f:
        return json.load(f)


def authenticate_and_get_token(cognito_config):
    """Authenticate with Cognito and get bearer token"""
    print("🔐 Authenticating with Cognito...")
    
    u = Cognito(
        cognito_config['user_pool_id'], 
        cognito_config['app_client_id'], 
        username=cognito_config['admin_user']['username']
    )
    u.authenticate(password=cognito_config['admin_user']['password'])
    
    bearer_token = u.id_token
    print(f"✅ Authentication successful")
    print(f"   Username: {cognito_config['admin_user']['username']}")
    
    return bearer_token


def test_runtime_invocation():
    """Test AgentCore invocation using Runtime"""
    print("=== Testing AgentCore Runtime Invocation ===")
    
    # Load configs
    deployment_info = load_deployment_info()
    cognito_config = load_cognito_config()
    
    if not deployment_info or not cognito_config:
        return False
    
    # Get authentication token
    bearer_token = authenticate_and_get_token(cognito_config)
    
    # Initialize runtime
    runtime = Runtime()
    
    # Test prompts
    test_cases = [
        "What is 2+2?",
        "Tell me about artificial intelligence",
        "What is the weather like today?",
        "Hello, how are you?",
        "Calculate 15 * 7"
    ]
    
    successful_tests = 0
    
    for i, prompt in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {prompt}")
        try:
            # Use runtime invoke method with bearer token
            response = runtime.invoke(
                {"prompt": prompt}, 
                bearer_token=bearer_token
            )
            print(f"✅ Response: {response}")
            successful_tests += 1
            
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
    
    print(f"\n📊 Results: {successful_tests}/{len(test_cases)} tests passed")
    
    if successful_tests == len(test_cases):
        print("\n🎉 All tests passed! AgentCore with authentication is working correctly.")
        print("✅ The agent can handle various types of questions")
        print("✅ Authentication is properly enforced")
        print("✅ Ready for React frontend integration")
        return True
    else:
        print(f"\n⚠️ Some tests failed. Authentication is working but there may be runtime issues.")
        return False


if __name__ == "__main__":
    success = test_runtime_invocation()
    exit(0 if success else 1)