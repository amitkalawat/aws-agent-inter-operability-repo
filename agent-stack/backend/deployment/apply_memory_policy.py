#!/usr/bin/env python3
"""
Apply Memory IAM Policy to AgentCore Execution Role
"""

import json
import boto3
import os
from botocore.exceptions import ClientError


def load_deployment_info():
    """Load deployment information to get the execution role"""
    deployment_file = 'deployment_info_auth.json'
    
    if not os.path.exists(deployment_file):
        print(f"❌ Deployment info not found: {deployment_file}")
        print("   Run deploy_agent_with_auth.py first")
        return None
    
    try:
        with open(deployment_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading deployment info: {e}")
        return None


def get_execution_role_name():
    """Extract role name from ARN"""
    deployment_info = load_deployment_info()
    if not deployment_info:
        return None
    
    # Get role name from the standard AgentCore pattern
    region = deployment_info.get('region', 'eu-central-1')
    role_name = f"AmazonBedrockAgentCoreSDKRuntime-{region}-6deb7df49a"
    
    print(f"🔍 Using execution role: {role_name}")
    return role_name


def apply_memory_policy():
    """Apply memory policy to the execution role"""
    role_name = get_execution_role_name()
    if not role_name:
        return False
    
    # Load memory policy
    policy_file = 'memory-policy.json'
    if not os.path.exists(policy_file):
        print(f"❌ Memory policy file not found: {policy_file}")
        return False
    
    try:
        with open(policy_file, 'r') as f:
            policy_document = f.read()
        
        # Apply policy to role
        iam_client = boto3.client('iam')
        policy_name = "BedrockAgentCoreMemoryPolicy"
        
        print(f"🔧 Applying memory policy to role: {role_name}")
        
        response = iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=policy_document
        )
        
        print(f"✅ Memory policy applied successfully!")
        print(f"   Policy Name: {policy_name}")
        print(f"   Role Name: {role_name}")
        
        # Verify the policy was applied
        try:
            get_response = iam_client.get_role_policy(
                RoleName=role_name,
                PolicyName=policy_name
            )
            print(f"✅ Policy verification successful")
            
        except ClientError as verify_error:
            print(f"⚠️  Could not verify policy: {verify_error}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchEntity':
            print(f"❌ Role not found: {role_name}")
            print("   Make sure the agent has been deployed first")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied applying policy to role: {role_name}")
            print("   Make sure you have IAM permissions to modify roles")
        else:
            print(f"❌ Error applying policy: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main function"""
    print("=== Apply Memory Policy to AgentCore Execution Role ===")
    
    success = apply_memory_policy()
    
    if success:
        print(f"\n=== Memory Policy Applied Successfully ===")
        print(f"✅ Memory permissions have been added to the execution role")
        print(f"✅ The agent should now be able to create and access memory")
        print(f"✅ Test memory functionality by redeploying the agent")
    else:
        print(f"\n=== Memory Policy Application Failed ===")
        print(f"❌ Please check the error messages above")
        print(f"❌ Ensure you have proper IAM permissions")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)