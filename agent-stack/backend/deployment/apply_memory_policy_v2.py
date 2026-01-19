#!/usr/bin/env python3
"""
Apply memory permissions to the new acme_chatbot_v2 agent's IAM role
"""

import boto3
import json

def apply_memory_policy():
    """Apply memory policy to the new agent's IAM role"""
    
    # IAM role for the new agent
    role_name = "AmazonBedrockAgentCoreSDKRuntime-eu-central-1-c6a89dea3a"
    policy_name = "BedrockAgentCoreMemoryPolicy-acme_chatbot_v2"
    
    # Read the memory policy
    with open('memory-policy.json', 'r') as f:
        policy_document = f.read()
    
    # Apply the policy
    iam_client = boto3.client('iam', region_name='eu-central-1')
    
    try:
        response = iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=policy_document
        )
        print(f"✅ Memory policy applied successfully to {role_name}")
        print(f"   Policy name: {policy_name}")
        return True
    except Exception as e:
        print(f"❌ Error applying memory policy: {e}")
        return False

if __name__ == "__main__":
    apply_memory_policy()