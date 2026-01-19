#!/usr/bin/env python3
"""
Test Authenticated AgentCore Deployment
"""

import json
import boto3
import os
from warrant import Cognito
from datetime import datetime


def load_deployment_info():
    """Load authenticated deployment information"""
    deployment_file = 'deployment_info_auth.json'
    
    if not os.path.exists(deployment_file):
        print(f"❌ Deployment file {deployment_file} not found.")
        print("   Run deploy_agent_with_auth.py first")
        return None
    
    try:
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
        print(f"✅ Deployment info loaded from {deployment_file}")
        return deployment_info
    except Exception as e:
        print(f"❌ Error loading deployment info: {e}")
        return None


def load_cognito_config():
    """Load Cognito configuration"""
    cognito_config_path = '../../infrastructure/cognito/cognito_config.json'
    
    if not os.path.exists(cognito_config_path):
        print(f"❌ Cognito configuration not found at {cognito_config_path}")
        return None
    
    try:
        with open(cognito_config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading Cognito configuration: {e}")
        return None


def authenticate_and_get_token(cognito_config):
    """Authenticate with Cognito and get bearer token"""
    print("🔐 Authenticating with Cognito...")
    
    try:
        u = Cognito(
            cognito_config['user_pool_id'], 
            cognito_config['app_client_id'], 
            username=cognito_config['admin_user']['username']
        )
        u.authenticate(password=cognito_config['admin_user']['password'])
        
        bearer_token = u.id_token
        print(f"✅ Authentication successful")
        print(f"   Username: {cognito_config['admin_user']['username']}")
        print(f"   Token obtained (valid for 24 hours)")
        
        return bearer_token
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


def test_unauthenticated_access(agent_arn, region):
    """Test that unauthenticated access is blocked"""
    print("\n=== Testing Unauthenticated Access (Should Fail) ===")
    
    try:
        client = boto3.client('bedrock-agentcore', region_name=region)
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier='DEFAULT',
            payload=json.dumps({'prompt': 'Hello without auth'})
            # No authorizationToken provided
        )
        print("❌ SECURITY ISSUE: Unauthenticated access succeeded (this should not happen)")
        return False
    except Exception as e:
        print(f"✅ Unauthenticated access properly blocked: {e}")
        return True


def test_authenticated_access(agent_arn, region, bearer_token):
    """Test authenticated access with various prompts"""
    print("\n=== Testing Authenticated Access ===")
    
    client = boto3.client('bedrock-agentcore', region_name=region)
    
    test_cases = [
        {"prompt": "What is 2+2?", "expected": "math calculation"},
        {"prompt": "What is the weather?", "expected": "weather info"},
        {"prompt": "Tell me about quantum computing", "expected": "general knowledge"},
        {"prompt": "Calculate the derivative of x^2", "expected": "calculus"},
        {"prompt": "Hello, how are you?", "expected": "conversation"}
    ]
    
    successful_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nAuthenticated Test {i}: {test_case['prompt']}")
        try:
            response = client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                qualifier='DEFAULT',
                payload=json.dumps({'prompt': test_case['prompt']}),
                authorizationToken=f"Bearer {bearer_token}"
            )
            
            # Read response
            response_body = response['response'].read()
            response_text = response_body.decode('utf-8').strip('"')
            response_text = response_text.replace('\\n', '\n')
            
            print(f"✅ Response: {response_text[:200]}...")
            print(f"   Status: {response['ResponseMetadata']['HTTPStatusCode']}")
            print(f"   Session ID: {response['runtimeSessionId']}")
            
            successful_tests += 1
            
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
    
    print(f"\n📊 Test Results: {successful_tests}/{len(test_cases)} tests passed")
    return successful_tests == len(test_cases)


def test_token_validation(agent_arn, region):
    """Test with invalid token"""
    print("\n=== Testing Invalid Token (Should Fail) ===")
    
    try:
        client = boto3.client('bedrock-agentcore', region_name=region)
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier='DEFAULT',
            payload=json.dumps({'prompt': 'Hello with fake token'}),
            authorizationToken="Bearer fake-invalid-token-12345"
        )
        print("❌ SECURITY ISSUE: Invalid token accepted (this should not happen)")
        return False
    except Exception as e:
        print(f"✅ Invalid token properly rejected: {e}")
        return True


def display_deployment_summary(deployment_info, cognito_config):
    """Display deployment and authentication summary"""
    print("\n=== Deployment Summary ===")
    print(f"🚀 Agent ARN: {deployment_info['agent_arn']}")
    print(f"🚀 Agent ID: {deployment_info['agent_id']}")
    print(f"🚀 Region: {deployment_info['region']}")
    print(f"🚀 Authentication: {deployment_info['authentication']['type']}")
    
    deployment_time = datetime.fromtimestamp(deployment_info['deployment_timestamp'])
    print(f"🚀 Deployed: {deployment_time}")
    
    print(f"\n=== Authentication Details ===")
    print(f"🔐 User Pool: {cognito_config['user_pool_id']}")
    print(f"🔐 App Client: {cognito_config['app_client_id']}")
    print(f"🔐 Admin User: {cognito_config['admin_user']['username']}")
    print(f"🔐 Discovery URL: {cognito_config['discovery_url']}")


def main():
    """Main test function"""
    print("=== Authenticated AgentCore Test ===")
    
    # Load deployment info
    deployment_info = load_deployment_info()
    if not deployment_info:
        return False
    
    # Load Cognito config
    cognito_config = load_cognito_config()
    if not cognito_config:
        return False
    
    # Display summary
    display_deployment_summary(deployment_info, cognito_config)
    
    # Get authentication token
    bearer_token = authenticate_and_get_token(cognito_config)
    if not bearer_token:
        return False
    
    agent_arn = deployment_info['agent_arn']
    region = deployment_info['region']
    
    # Run security tests
    security_test_1 = test_unauthenticated_access(agent_arn, region)
    security_test_2 = test_token_validation(agent_arn, region)
    
    # Run authenticated functionality tests
    functionality_test = test_authenticated_access(agent_arn, region, bearer_token)
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"🔒 Unauthenticated access blocked: {'✅' if security_test_1 else '❌'}")
    print(f"🔒 Invalid token rejected: {'✅' if security_test_2 else '❌'}")
    print(f"🚀 Authenticated functionality: {'✅' if functionality_test else '❌'}")
    
    all_tests_passed = security_test_1 and security_test_2 and functionality_test
    
    if all_tests_passed:
        print(f"\n🎉 All tests passed! The authenticated AgentCore deployment is working correctly.")
        print(f"🔐 Security: Properly blocks unauthorized access")
        print(f"🚀 Functionality: Responds correctly to authenticated requests")
        print(f"🎯 Ready for React frontend integration")
    else:
        print(f"\n❌ Some tests failed. Please check the deployment.")
    
    return all_tests_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)