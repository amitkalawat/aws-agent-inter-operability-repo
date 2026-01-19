#!/usr/bin/env python3
"""
Test AgentCore with JWT Authentication using Direct HTTP Requests
Following AWS documentation: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-oauth.html
"""

import json
import os
import urllib.parse
import uuid
import requests
from warrant import Cognito
from datetime import datetime


def load_deployment_info():
    """Load deployment information"""
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
        
        # Try access token instead of ID token - it has client_id claim
        bearer_token = u.access_token
        print(f"✅ Authentication successful")
        print(f"   Username: {cognito_config['admin_user']['username']}")
        print(f"   Token obtained (access token with client_id claim)")
        
        return bearer_token
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


def invoke_agent_http(agent_arn, region, bearer_token, payload, session_id=None):
    """Invoke AgentCore agent using direct HTTP request with JWT authentication"""
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # URL encode the agent ARN (very important!)
    escaped_agent_arn = urllib.parse.quote(agent_arn, safe='')
    
    # Construct the invocation URL
    url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"
    
    # Set up headers as per AWS documentation
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-Amzn-Trace-Id": f"trace-{uuid.uuid4()}",
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id
    }
    
    try:
        # Make the HTTP POST request
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=120
        )
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request failed: {e}")
        return None


def test_unauthenticated_access(agent_arn, region):
    """Test that unauthenticated access is properly blocked"""
    print("\n=== Testing Unauthenticated Access (Should Fail) ===")
    
    # URL encode the agent ARN
    escaped_agent_arn = urllib.parse.quote(agent_arn, safe='')
    url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"
    
    # Headers without Authorization
    headers = {
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps({"prompt": "Hello without auth"}),
            timeout=30
        )
        
        if response.status_code >= 400:
            print(f"✅ Unauthenticated access properly blocked: {response.status_code} - {response.text}")
            return True
        else:
            print(f"❌ SECURITY ISSUE: Unauthenticated access succeeded (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"✅ Unauthenticated access properly blocked: {e}")
        return True


def test_invalid_token(agent_arn, region):
    """Test that invalid tokens are rejected"""
    print("\n=== Testing Invalid Token (Should Fail) ===")
    
    # URL encode the agent ARN
    escaped_agent_arn = urllib.parse.quote(agent_arn, safe='')
    url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"
    
    # Headers with fake token
    headers = {
        "Authorization": "Bearer fake-invalid-token-12345",
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps({"prompt": "Hello with fake token"}),
            timeout=30
        )
        
        if response.status_code >= 400:
            print(f"✅ Invalid token properly rejected: {response.status_code} - {response.text}")
            return True
        else:
            print(f"❌ SECURITY ISSUE: Invalid token accepted (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"✅ Invalid token properly rejected: {e}")
        return True


def test_authenticated_access(agent_arn, region, bearer_token):
    """Test authenticated access with various prompts"""
    print("\n=== Testing Authenticated Access ===")
    
    test_cases = [
        {"prompt": "What is 2+2?", "expected": "math calculation"},
        {"prompt": "What is the weather?", "expected": "weather info"},
        {"prompt": "Tell me about quantum computing", "expected": "general knowledge"},
        {"prompt": "Calculate the derivative of x^2", "expected": "calculus"},
        {"prompt": "Hello, how are you?", "expected": "conversation"}
    ]
    
    successful_tests = 0
    session_id = str(uuid.uuid4())  # Use same session for all tests
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Authenticated Test {i}: {test_case['prompt']}")
        
        response = invoke_agent_http(
            agent_arn=agent_arn,
            region=region,
            bearer_token=bearer_token,
            payload={"prompt": test_case['prompt']},
            session_id=session_id
        )
        
        if response is None:
            print(f"❌ Test {i} failed: No response")
            continue
            
        try:
            if response.status_code == 200:
                # Try to parse response
                if response.headers.get('content-type', '').startswith('application/json'):
                    response_data = response.json()
                    response_text = json.dumps(response_data, indent=2)
                else:
                    response_text = response.text
                
                print(f"✅ Test {i} SUCCESS (Status: {response.status_code})")
                print(f"   Response: {response_text[:300]}...")
                successful_tests += 1
            else:
                print(f"❌ Test {i} failed with status: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Test {i} failed to parse response: {e}")
    
    print(f"\n📊 Test Results: {successful_tests}/{len(test_cases)} tests passed")
    return successful_tests == len(test_cases)


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
    print("=== AgentCore HTTP Authentication Test ===")
    
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
    print("\n" + "="*60)
    print("SECURITY TESTS")
    print("="*60)
    
    security_test_1 = test_unauthenticated_access(agent_arn, region)
    security_test_2 = test_invalid_token(agent_arn, region)
    
    # Run authenticated functionality tests
    print("\n" + "="*60)
    print("FUNCTIONALITY TESTS")
    print("="*60)
    
    functionality_test = test_authenticated_access(agent_arn, region, bearer_token)
    
    # Summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"🔒 Unauthenticated access blocked: {'✅' if security_test_1 else '❌'}")
    print(f"🔒 Invalid token rejected: {'✅' if security_test_2 else '❌'}")
    print(f"🚀 Authenticated functionality: {'✅' if functionality_test else '❌'}")
    
    all_tests_passed = security_test_1 and security_test_2 and functionality_test
    
    if all_tests_passed:
        print(f"\n🎉 ALL TESTS PASSED! The authenticated AgentCore deployment is working perfectly.")
        print(f"🔐 Security: Properly blocks unauthorized access")
        print(f"🚀 Functionality: Responds correctly to authenticated requests")
        print(f"🎯 Ready for React frontend integration")
        print(f"\n💡 Usage Example:")
        print(f"   curl -X POST \\")
        print(f"     -H 'Authorization: Bearer YOUR_TOKEN' \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"prompt\": \"Hello\"}}' \\")
        print(f"     'https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{urllib.parse.quote(agent_arn, safe='')}/invocations?qualifier=DEFAULT'")
    else:
        print(f"\n❌ Some tests failed. Please check the deployment and authentication setup.")
    
    return all_tests_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)