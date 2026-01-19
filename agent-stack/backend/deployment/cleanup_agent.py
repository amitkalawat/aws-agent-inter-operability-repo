#!/usr/bin/env python3
"""
Cleanup Amazon Bedrock AgentCore deployment
"""

import json
import boto3
import os
from boto3.session import Session


def load_deployment_info():
    """Load deployment information from file"""
    deployment_file = 'deployment_info.json'
    
    if not os.path.exists(deployment_file):
        print(f"Error: {deployment_file} not found. Cannot proceed with cleanup.")
        print("Make sure you have run deploy_agent.py first.")
        return None
    
    try:
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
        print(f"Loaded deployment info from {deployment_file}")
        return deployment_info
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {deployment_file}")
        return None
    except Exception as e:
        print(f"Error loading deployment info: {e}")
        return None


def delete_agent_runtime(deployment_info):
    """Delete the AgentCore runtime"""
    print("\n=== Deleting Agent Runtime ===")
    
    try:
        region = deployment_info['region']
        agent_id = deployment_info['agent_id']
        
        agentcore_control_client = boto3.client('bedrock-agentcore-control', region_name=region)
        
        print(f"Deleting agent runtime: {agent_id}")
        response = agentcore_control_client.delete_agent_runtime(
            agentRuntimeId=agent_id
        )
        
        print(f"Agent runtime deletion initiated: {response}")
        return True
        
    except Exception as e:
        print(f"Error deleting agent runtime: {e}")
        return False


def delete_ecr_repository(deployment_info):
    """Delete the ECR repository"""
    print("\n=== Deleting ECR Repository ===")
    
    try:
        region = deployment_info['region']
        ecr_uri = deployment_info['ecr_uri']
        
        # Extract repository name from ECR URI
        # Format: account.dkr.ecr.region.amazonaws.com/repository_name:tag
        repository_name = ecr_uri.split('/')[1].split(':')[0]
        
        ecr_client = boto3.client('ecr', region_name=region)
        
        print(f"Deleting ECR repository: {repository_name}")
        response = ecr_client.delete_repository(
            repositoryName=repository_name,
            force=True  # Force deletion even if repository contains images
        )
        
        print(f"ECR repository deleted: {response}")
        return True
        
    except Exception as e:
        print(f"Error deleting ECR repository: {e}")
        return False


def cleanup_local_files():
    """Clean up local deployment files"""
    print("\n=== Cleaning Up Local Files ===")
    
    files_to_remove = ['deployment_info.json']
    
    for file_path in files_to_remove:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed: {file_path}")
            else:
                print(f"File not found (already cleaned): {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")


def main():
    """Main cleanup function"""
    print("=== Amazon Bedrock AgentCore Cleanup ===")
    
    # Load deployment information
    deployment_info = load_deployment_info()
    if not deployment_info:
        return False
    
    print(f"Agent ID: {deployment_info.get('agent_id')}")
    print(f"ECR URI: {deployment_info.get('ecr_uri')}")
    print(f"Agent ARN: {deployment_info.get('agent_arn')}")
    print(f"Region: {deployment_info.get('region')}")
    
    # Confirm cleanup
    response = input("\nAre you sure you want to delete all resources? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Cleanup cancelled.")
        return False
    
    success = True
    
    # Delete agent runtime
    if not delete_agent_runtime(deployment_info):
        success = False
    
    # Delete ECR repository
    if not delete_ecr_repository(deployment_info):
        success = False
    
    # Clean up local files
    cleanup_local_files()
    
    if success:
        print("\n=== Cleanup Complete ===")
        print("All resources have been successfully cleaned up.")
    else:
        print("\n=== Cleanup Completed with Errors ===")
        print("Some resources may not have been cleaned up properly.")
        print("Please check the AWS console and clean up manually if needed.")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)