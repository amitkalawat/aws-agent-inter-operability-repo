# ACME Corp Backend Deployment Architecture

## Overview

The ACME Corp Bedrock AgentCore chatbot represents a sophisticated multi-layered system that combines three key architectural components:

1. **Strands Framework**: Agent orchestration and tool management
2. **AWS Bedrock AgentCore**: Serverless runtime deployment platform  
3. **MCP (Model Context Protocol)**: External service integration via remote servers

This document provides detailed technical insights into how these components work together to deliver a production-ready, scalable chatbot system with advanced tool integration capabilities.

---

## 1. Strands Framework Integration

### Core Components

The Strands framework serves as the orchestration layer for our AI agent, combining local tools with remote MCP capabilities.

#### Agent Configuration
```python
from strands import Agent, tool
from strands.models import BedrockModel

model_id = "eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
model = BedrockModel(model_id=model_id)

# Agent with context-aware system prompt and mixed tool set
agent = Agent(
    model=model, 
    tools=all_tools,  # Combination of local and MCP tools
    system_prompt=system_prompt
)
```

#### Local Tool Integration
```python
@tool
def execute_code_with_visualization(
    code: str, 
    description: str = "Execute Python code for data analysis and visualization"
) -> str:
    """Execute Python code using code_session context manager for visualization.
    Supports pandas and matplotlib for creating charts and analyzing data."""
    
    # Integration with Bedrock Code Interpreter
    with code_session(CODE_INTERPRETER_REGION) as code_client:
        response = code_client.invoke("executeCode", {
            "code": modified_code,
            "language": "python",
            "clearContext": False
        })
        # Process and return results
```

#### Streaming Architecture
The agent supports real-time streaming responses with custom event processing:

```python
async def strands_agent_bedrock_streaming(payload):
    """Async streaming entrypoint with real-time responses"""
    
    streaming_agent = Agent(model=model, tools=all_tools, system_prompt=system_prompt)
    
    async for event in streaming_agent.stream_async(user_input):
        chunk = extract_text_from_event(event)
        if chunk:
            full_response += chunk
            yield chunk
```

#### Custom Event Processing
```python
def extract_text_from_event(event) -> str:
    """Extract text content from Strands streaming event structure"""
    
    # Handle nested event structure from Strands
    if 'event' in event and 'contentBlockDelta' in event['event']:
        delta = event['event']['contentBlockDelta']
        if 'delta' in delta and 'text' in delta['delta']:
            return str(delta['delta']['text'])
    
    # Handle callback event structure
    if 'callback' in event and isinstance(event['callback'], str):
        return event['callback']
    
    return ""
```

### Memory Integration
Strands integrates with AWS Bedrock AgentCore Memory for conversation persistence:

```python
# Memory configuration per user session
memory_name = f"ACMEChatMemory_{hashlib.md5(actor_id.encode()).hexdigest()[:8]}"

memory_hooks = create_memory_manager(
    memory_name=memory_name,
    actor_id=actor_id,
    session_id=session_id,
    region="eu-central-1"
)

# Retrieve conversation context
conversation_context = memory_hooks.retrieve_conversation_context(user_input)
```

---

## 2. AWS Bedrock AgentCore Deployment

### Runtime Platform Architecture

AgentCore provides a serverless container deployment platform specifically designed for AI agents.

#### Configuration File Structure
**`.bedrock_agentcore.yaml`**:
```yaml
default_agent: strands_claude_getting_started_auth
agents:
  strands_claude_getting_started_auth:
    name: strands_claude_getting_started_auth
    entrypoint: /path/to/strands_claude.py
    platform: linux/arm64
    container_runtime: docker
    aws:
      execution_role: arn:aws:iam::ACCOUNT:role/RUNTIME_ROLE
      region: eu-central-1
      ecr_repository: ACCOUNT.dkr.ecr.REGION.amazonaws.com/REPO
      network_configuration:
        network_mode: PUBLIC
      protocol_configuration:
        server_protocol: HTTP
    authorizer_configuration:
      customJWTAuthorizer:
        discoveryUrl: https://cognito-idp.REGION.amazonaws.com/POOL_ID/.well-known/openid-configuration
        allowedClients: [CLIENT_ID]
```

#### Deployment Script Architecture
**`deploy_agent_with_auth.py`**:
```python
from bedrock_agentcore_starter_toolkit import Runtime

def main():
    # Initialize AgentCore Runtime
    agentcore_runtime = Runtime()
    
    # Configure with Cognito JWT authentication
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
                "allowedClients": [cognito_config["app_client_id"]]
            }
        }
    )
    
    # Launch the containerized agent
    launch_result = agentcore_runtime.launch()
```

#### Container Build Process
**Dockerfile** (Auto-generated):
```dockerfile
FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install aws-opentelemetry-distro>=0.10.1

# Set AWS environment
ENV AWS_REGION=eu-central-1
ENV AWS_DEFAULT_REGION=eu-central-1
ENV DOCKER_CONTAINER=1

# Security: non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8080
EXPOSE 8000

# Copy agent files (must be in deployment directory)
COPY . .

# Start with OpenTelemetry instrumentation
CMD ["opentelemetry-instrument", "python", "-m", "strands_claude"]
```

### Critical Deployment Requirements

#### File Structure Requirement
```bash
# Files MUST be copied to deployment directory before deployment
backend/deployment/
├── strands_claude.py        # Main agent (copied from ../agent/)
├── memory_manager.py        # Memory functionality (copied)
├── secrets_manager.py       # Secrets handling (copied)
├── requirements.txt         # Dependencies (copied)
├── Dockerfile              # Container definition (auto-generated)
├── deploy_agent_with_auth.py # Deployment script
└── .bedrock_agentcore.yaml  # AgentCore configuration (auto-generated)
```

#### Unified Entrypoint Pattern
```python
@app.entrypoint
async def strands_agent_bedrock_unified(payload, context=None):
    """Routes between streaming and non-streaming based on request parameters"""
    
    # Detect streaming mode from query parameters or headers
    streaming_enabled = False
    if context and hasattr(context, 'request'):
        query_params = str(context.request.url.query)
        streaming_enabled = "streaming=true" in query_params
        
        accept_header = context.request.headers.get('accept', '')
        streaming_enabled = streaming_enabled or 'text/event-stream' in accept_header
    
    # Route to appropriate handler
    if streaming_enabled:
        return strands_agent_bedrock_streaming(payload)
    else:
        return strands_agent_bedrock(payload)
```

### Authentication & Authorization

#### Cognito JWT Integration
```python
def load_cognito_config():
    """Load Cognito configuration for JWT validation"""
    cognito_config_path = '../../infrastructure/cognito/cognito_config.json'
    
    with open(cognito_config_path, 'r') as f:
        cognito_config = json.load(f)
    
    return {
        'user_pool_id': cognito_config['user_pool_id'],
        'app_client_id': cognito_config['app_client_id'], 
        'discovery_url': cognito_config['discovery_url']
    }
```

---

## 3. MCP (Model Context Protocol) Integration Architecture

### Overview
The system integrates with multiple MCP servers running on AgentCore, each providing specialized capabilities through remote tool access.

### MCP Server Types Deployed

#### 1. AWS Documentation MCP Server
**Purpose**: Real-time AWS service documentation access
**Tools**: `read_documentation`, `search_documentation`, `recommend`
**Runtime**: `arn:aws:bedrock-agentcore:eu-central-1:241533163649:runtime/aws_doc_mcp_server_ibc-8F7VmKAEcL`

#### 2. Data Processing MCP Server  
**Purpose**: Athena, Glue, EMR tools for data analytics
**Tools**: Query execution, data catalog management, ETL operations
**Databases**: `acme_streaming_data`, `acme_telemetry`

#### 3. Nova Canvas MCP Server
**Purpose**: AI image generation with Amazon Nova Canvas
**Tools**: `generate_image` with CloudFront URL delivery
**Integration**: S3 storage with presigned URLs

### MCP Authentication Architecture

#### Token Management System
```python
class MCPManager:
    """Manages MCP client creation and bearer token authentication"""
    
    def __init__(self):
        self._bearer_token: Optional[str] = None
        self._token_expires_at: float = 0
    
    def _get_bearer_token(self) -> str:
        """Get bearer token from Cognito with 50-minute caching"""
        current_time = time.time()
        
        if self._bearer_token and current_time < self._token_expires_at:
            return self._bearer_token
        
        # OAuth2 client credentials flow
        credentials = secrets_manager.get_mcp_credentials()
        
        domain = f"mcp-registry-{account}-mcp-gateway-registry.auth.{region}.amazoncognito.com"
        token_url = f"https://{domain}/oauth2/token"
        
        response = requests.post(token_url, data={
            'grant_type': 'client_credentials',
            'client_id': credentials['MCP_COGNITO_CLIENT_ID'],
            'client_secret': credentials['MCP_COGNITO_CLIENT_SECRET'],
            'scope': 'mcp-registry/read mcp-registry/write'
        })
        
        token_data = response.json()
        self._bearer_token = token_data['access_token']
        self._token_expires_at = current_time + (50 * 60)  # 50-minute cache
        
        return self._bearer_token
```

#### HTTP Transport Creation
```python
def create_aws_docs_transport(self):
    """Create AWS Documentation MCP transport"""
    credentials = secrets_manager.get_mcp_credentials()
    bearer_token = self._get_bearer_token()
    
    aws_docs_url = credentials['MCP_DOCS_URL']
    headers = {"Authorization": f"Bearer {bearer_token}"}
    
    return streamablehttp_client(aws_docs_url, headers=headers)

def create_aws_docs_client(self) -> MCPClient:
    """Create MCP client for AWS Documentation"""
    client = MCPClient(lambda: self.create_aws_docs_transport())
    return client
```

### MCP Server Deployment on AgentCore

#### FastMCP Wrapper Pattern
MCP servers use a wrapper pattern to convert stdio-based servers to HTTP endpoints:

```python
# mcp-server.py - FastMCP wrapper for AgentCore deployment
import sys
import os
sys.path.insert(0, os.path.abspath("./aws-documentation-mcp-server"))

from mcp.server.fastmcp import FastMCP
from awslabs.aws_documentation_mcp_server.server_aws import (
    read_documentation, search_documentation, recommend
)

mcp = FastMCP(
    'awslabs.aws-documentation-mcp-server',
    host="0.0.0.0",
    stateless_http=True,
    instructions=instructions,
    dependencies=['pydantic', 'httpx', 'beautifulsoup4', 'loguru']
)

# Register tools
mcp.tool(name='read_documentation')(read_documentation)
mcp.tool(name='search_documentation')(search_documentation)
mcp.tool(name='recommend')(recommend)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

#### MCP Server AgentCore Configuration
```yaml
# .bedrock_agentcore.yaml for MCP servers
agents:
  aws_doc_mcp_server_ibc:
    name: aws_doc_mcp_server_ibc
    entrypoint: mcp-server.py
    platform: linux/arm64
    container_runtime: docker
    authorizer_configuration:
      customJWTAuthorizer:
        discoveryUrl: https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_PaVtjk8dt/.well-known/openid-configuration
        allowedClients: [4rit5a00iqft9ak8sl5hb28sr]
```

### Tool Registration and Invocation

#### Dynamic Tool Discovery
```python
def create_agent_with_memory(payload: dict):
    """Create agent with dynamically discovered MCP tools"""
    
    # Create MCP clients
    aws_docs_client = mcp_manager.create_aws_docs_client()
    dataproc_client = mcp_manager.create_dataproc_client()
    nova_canvas_client = mcp_manager.create_nova_canvas_client()
    
    # Nested context managers for all available clients
    with aws_docs_client:
        with dataproc_client:
            with nova_canvas_client:
                # Dynamically discover tools from each MCP server
                aws_tools = aws_docs_client.list_tools_sync()
                dataproc_tools = dataproc_client.list_tools_sync()
                nova_tools = nova_canvas_client.list_tools_sync()
                
                # Combine with local tools
                all_tools = aws_tools + dataproc_tools + nova_tools + [execute_code_with_visualization]
                
                # Create agent with full tool set
                agent = Agent(model=model, tools=all_tools, system_prompt=system_prompt)
                return agent
```

### Secrets Management Integration

#### AWS Secrets Manager Configuration
```python
class SecretsManager:
    """Manages MCP credentials securely"""
    
    def get_mcp_credentials(self) -> Dict[str, str]:
        """Get MCP credentials from AWS Secrets Manager"""
        secret_name = "acme-chatbot/mcp-credentials"
        
        credentials = self.get_secret(secret_name)
        
        # Validate required fields for MCP authentication
        required_fields = [
            'MCP_COGNITO_POOL_ID',
            'MCP_COGNITO_REGION', 
            'MCP_COGNITO_CLIENT_ID',
            'MCP_COGNITO_CLIENT_SECRET',
            'MCP_DOCS_URL'
        ]
        
        missing_fields = [field for field in required_fields if field not in credentials]
        if missing_fields:
            raise Exception(f"Missing required MCP fields: {missing_fields}")
        
        return credentials
```

---

## 4. Deployment Workflow

### Complete Deployment Process

#### Step 1: File Preparation
```bash
# CRITICAL: Copy agent files to deployment directory
cd backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/memory_manager.py .
cp ../agent/secrets_manager.py .
cp ../agent/requirements.txt .
```

#### Step 2: Agent Deployment
```bash
# Deploy the main Strands agent
source .venv/bin/activate
python deploy_agent_with_auth.py
```

#### Step 3: MCP Server Deployment  
```bash
# Deploy individual MCP servers (example: AWS Documentation)
cd aws-mcp-server-agentcore
python deploy_mcp_server.py
```

#### Step 4: Memory Permissions
```bash
# Apply AgentCore Memory permissions
cd backend/deployment
python apply_memory_policy.py
```

### Infrastructure Dependencies

#### IAM Roles and Policies
**Agent Execution Role**:
- Amazon Bedrock model invocation
- Amazon ECR image access
- CloudWatch logging permissions
- AgentCore Memory access
- Code Interpreter permissions

**MCP Server Roles**:
- Bedrock AgentCore runtime access
- Service-specific permissions (S3 for Nova Canvas, Athena for data processing)

#### AWS Services Integration
- **Amazon Cognito**: JWT authentication for both agent and MCP endpoints
- **Amazon ECR**: Container image storage
- **AWS CodeBuild**: ARM64 container building
- **Amazon S3**: Visualization storage and MCP asset delivery
- **AWS CloudWatch**: Logging and monitoring
- **AWS Secrets Manager**: Secure credential storage

### Monitoring and Observability

#### CloudWatch Integration
```bash
# View agent runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/strands_claude_getting_started_auth-nYQSK477I1-DEFAULT --region eu-central-1

# View MCP server logs  
aws logs tail /aws/bedrock-agentcore/runtimes/aws_doc_mcp_server_ibc-8F7VmKAEcL-DEFAULT --region eu-central-1
```

#### Health Checking
AgentCore provides built-in health checks and status monitoring:
```python
# Check deployment status
status_response = agentcore_runtime.status()
print(f"Agent status: {status_response.endpoint['status']}")
```

---

## 5. Key Architecture Benefits

### Scalability
- **Auto-scaling**: AgentCore manages container scaling based on demand
- **Serverless**: No infrastructure management required
- **Multi-region**: Can deploy across multiple AWS regions

### Security  
- **JWT Authentication**: Cognito-based authentication for all endpoints
- **IAM Integration**: Fine-grained permissions using AWS IAM
- **Secrets Management**: Secure credential storage and rotation
- **Network Isolation**: VPC-based networking with security groups

### Maintainability
- **Modular Design**: Separate MCP servers for different capabilities
- **Version Control**: Container-based deployment with image versioning  
- **Configuration Management**: YAML-based configuration with environment-specific settings
- **Automated Deployment**: Infrastructure-as-code with deployment scripts

### Extensibility
- **Plugin Architecture**: Easy addition of new MCP servers
- **Tool Discovery**: Dynamic tool registration from remote servers
- **Protocol Flexibility**: Support for both streaming and non-streaming interactions
- **Multi-model Support**: Framework supports different LLM models

---

## 6. Troubleshooting Guide

### Common Issues

#### File Not Found During Deployment
**Problem**: Agent files not found during container build
**Solution**: Ensure all agent files are copied to the deployment directory:
```bash
cd backend/deployment
cp ../agent/*.py .
cp ../agent/requirements.txt .
```

#### MCP Authentication Failures
**Problem**: Bearer token authentication failing
**Solution**: Verify MCP credentials in Secrets Manager and token caching:
```python
# Force token refresh
mcp_manager._bearer_token = None
mcp_manager._token_expires_at = 0
```

#### Memory Permission Errors
**Problem**: AgentCore Memory access denied
**Solution**: Apply memory policies to execution role:
```bash
cd backend/deployment
python apply_memory_policy.py
```

#### Container Build Failures
**Problem**: CodeBuild failing with ARM64 platform
**Solution**: Verify Dockerfile platform specification and dependency compatibility

### Debugging Commands
```bash
# Check agent logs
aws logs tail /aws/bedrock-agentcore/runtimes/AGENT_ID-DEFAULT --follow

# Test MCP connectivity
python mcp_client_remote.py

# Verify IAM permissions
aws iam get-role --role-name EXECUTION_ROLE_NAME

# Check ECR repositories
aws ecr describe-repositories --region eu-central-1
```

---

This architecture represents a production-ready, enterprise-grade chatbot system that leverages cutting-edge AWS services while maintaining security, scalability, and maintainability principles. The modular design allows for easy extension and modification as requirements evolve.