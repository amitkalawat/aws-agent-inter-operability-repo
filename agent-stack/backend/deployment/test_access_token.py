#!/usr/bin/env python3
"""
Test main agent with Access Token authentication calling MCP AWS Documentation tools
"""

import json
import boto3
import requests
import time

def get_access_token():
    """Get Cognito access token using boto3 (same way as updated strands_claude.py)"""
    try:
        # Load cognito config
        with open('../../infrastructure/cognito/cognito_config.json', 'r') as f:
            cognito_config = json.load(f)
        
        # Use boto3 cognito-idp client
        client = boto3.client('cognito-idp', region_name='eu-central-1')
        
        # Authenticate and get tokens
        response = client.initiate_auth(
            ClientId=cognito_config['app_client_id'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': cognito_config['admin_user']['username'],
                'PASSWORD': cognito_config['admin_user']['password']
            }
        )
        
        # Return the Access token (has client_id claim needed for AgentCore)
        return response['AuthenticationResult']['AccessToken']
        
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def test_main_agent_with_aws_docs():
    """Test main agent with AWS documentation query"""
    print("=== Testing Main Agent with AWS Documentation Tools ===")
    
    # Get access token
    print("Getting access token...")
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get access token")
        return False
    print("✅ Access token obtained")
    
    # Load deployment info for acme_chatbot_v2
    try:
        with open('deployment_info_v2.json', 'r') as f:
            deployment_info = json.load(f)
        agent_arn = deployment_info['agent_arn']
        print(f"✅ Agent ARN: {agent_arn}")
    except Exception as e:
        print(f"❌ Error loading deployment info: {e}")
        return False
    
    # Test with MCP tools that should trigger OAuth authentication
    test_queries = [
        "Can you search AWS documentation for information about S3 bucket policies?",  # AWS Docs MCP
        "Create an image of a sunset over mountains using Nova Canvas",  # Nova Canvas MCP
        "What is the weather?",  # Basic test
        "What is 5+3?"  # Calculator test
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        
        try:
            # Use requests to call AgentCore directly
            encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
            url = f"https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
            
            # Generate session ID that's at least 33 characters long (AWS requirement)
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
                print(f"✅ Response: {response.text[:500]}...")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during test {i}: {e}")
    
    return True

if __name__ == "__main__":
    test_main_agent_with_aws_docs()