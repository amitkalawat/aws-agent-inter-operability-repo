# Backend - Bedrock AgentCore

This directory contains the AgentCore backend implementation with Claude AI.

## Structure

- `agent/` - Agent source code and configuration
- `deployment/` - Deployment and cleanup scripts
- `docker/` - Docker configuration files
- `.bedrock_agentcore.yaml` - AgentCore configuration

## Deployment

1. Activate virtual environment:
   ```bash
   cd ../
   source agentcore-env/bin/activate
   ```

2. Deploy agent:
   ```bash
   cd backend/deployment
   export AWS_DEFAULT_REGION=eu-central-1
   python deploy_agent.py
   ```

3. Clean up resources:
   ```bash
   python cleanup_agent.py
   ```

## Agent Configuration

The agent (`agent/strands_claude.py`) includes:
- Claude 3.7 Sonnet model (EU region)
- Calculator tool for mathematical operations
- Weather tool for basic weather info
- General conversation capabilities

## Requirements

- Python 3.8+
- AWS CLI configured
- Virtual environment with dependencies from `agent/requirements.txt`