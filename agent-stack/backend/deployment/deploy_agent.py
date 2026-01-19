#!/usr/bin/env python3
"""
Deploy Strands Agent to Amazon Bedrock AgentCore
"""

import json
import boto3
import time
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session


def load_config():
    """Load configuration from config.json"""
    try:
        with open('../agent/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "agent_name": "strands_claude_getting_started",
            "entrypoint": "../agent/strands_claude.py",
            "requirements_file": "../agent/requirements.txt"
        }


def save_deployment_info(deployment_info):
    """Save deployment information for cleanup"""
    with open('deployment_info.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    print(f"Deployment info saved to deployment_info.json")


def test_deployment(agentcore_runtime, agent_arn):
    """Test the deployed agent with sample invocations"""
    print("\n=== Testing Deployed Agent ===")
    
    test_cases = [
        {"prompt": "What is the weather now?"},
        {"prompt": "What is 2+2?"},
        {"prompt": "Calculate 10 * 5 and tell me the weather"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['prompt']}")
        try:
            # Test with runtime invoke
            response = agentcore_runtime.invoke(test_case)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error during test {i}: {e}")
    
    # Test with boto3 client
    print(f"\n=== Testing with Boto3 Client ===")
    try:
        boto_session = Session()
        region = boto_session.region_name
        agentcore_client = boto3.client('bedrock-agentcore', region_name=region)
        
        boto3_response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps({"prompt": "What is 5+3?"})
        )
        print(f"Boto3 Response: {boto3_response}")
    except Exception as e:
        print(f"Boto3 test failed: {e}")


def main():
    """Main deployment function"""
    print("=== Amazon Bedrock AgentCore Deployment ===")
    
    # Load configuration
    config = load_config()
    print(f"Configuration loaded: {config}")
    
    # Set up AWS session
    boto_session = Session()
    region = boto_session.region_name
    print(f"Using AWS region: {region}")
    
    # Initialize runtime
    print("\n=== Initializing AgentCore Runtime ===")
    agentcore_runtime = Runtime()
    
    # Configure the agent
    print("\n=== Configuring Agent ===")
    try:
        response = agentcore_runtime.configure(
            entrypoint=config["entrypoint"],
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file=config["requirements_file"],
            region=region,
            agent_name=config["agent_name"]
        )
        print(f"Configuration response: {response}")
    except Exception as e:
        print(f"Error during configuration: {e}")
        return False
    
    # Launch the agent
    print("\n=== Launching Agent ===")
    try:
        launch_result = agentcore_runtime.launch()
        print(f"Launch successful!")
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
            "deployment_timestamp": time.time()
        }
        save_deployment_info(deployment_info)
        
        # Test the deployment
        test_deployment(agentcore_runtime, launch_result.agent_arn)
        
        print(f"\n=== Deployment Complete ===")
        print(f"Agent deployed successfully!")
        print(f"Agent ARN: {launch_result.agent_arn}")
        print(f"Use cleanup_agent.py to clean up resources when done.")
        
        return True
        
    except Exception as e:
        print(f"Error during launch: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)