# AWS MCP Server on AgentCore Runtime

A comprehensive guide and implementation for deploying Amazon Web Services Model Context Protocol (MCP) servers to Amazon Bedrock AgentCore Runtime, with a focus on the Amazon Rekognition MCP server.

## Overview

This project demonstrates how to take AWS MCP servers (originally designed for local stdio execution) and deploy them as scalable, cloud-native services using Amazon Bedrock AgentCore Runtime. The implementation includes local testing, authentication setup, containerization, and remote deployment.

## Features

### Amazon Rekognition MCP Server
The project includes a complete implementation of the Amazon Rekognition MCP server with 8 specialized tools:

**Face Management Tools:**
- `list_collections` - List all face collections in your AWS account
- `index_faces` - Add faces from images to a collection for future searching
- `search_faces_by_image` - Find matching faces in a collection using an input image
- `compare_faces` - Compare faces between two images for identity verification

**Image Analysis Tools:**
- `detect_labels` - Identify objects, scenes, activities, and concepts in images
- `detect_text` - Extract and recognize text from images (OCR)
- `detect_moderation_labels` - Detect inappropriate or unsafe content
- `recognize_celebrities` - Identify celebrities in images

### Deployment Pipeline
- **Local Testing**: Test MCP servers locally before deployment
- **Authentication**: Amazon Cognito JWT-based authentication
- **Containerization**: Automatic Docker image generation and ECR deployment
- **Runtime Management**: AgentCore Runtime deployment and monitoring
- **Remote Access**: Secure HTTPS endpoints with bearer token authentication

## Prerequisites

### System Requirements
- Python 3.10 or higher
- AWS CLI configured with valid credentials
- Docker installed (for containerization)
- Jupyter Notebook environment

### AWS Permissions
Your AWS credentials must have permissions for:
- Amazon Rekognition (full access recommended)
- Amazon Bedrock AgentCore
- Amazon ECR (for container registry)
- Amazon Cognito (for authentication)
- IAM (for role creation)
- AWS Systems Manager Parameter Store
- AWS Secrets Manager

## Quick Start

### 1. Clone and Setup
```bash
# Clone the AWS MCP repository
git clone https://github.com/awslabs/mcp.git

# Copy the Amazon Rekognition MCP server
cp -r ./mcp/src/amazon-rekognition-mcp-server ./

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file with your configuration:
```env
COGNITO_POOL_ID=your_pool_id
COGNITO_REGION=us-east-1
COGNITO_USERNAME=admin
COGNITO_CLIENT_SECRET=your_client_secret
COGNITO_PASSWORD=your_password
```

### 3. Run the Notebook
Open and execute `mcp-agentcore-runtime.ipynb` to:
1. Install dependencies
2. Test the MCP server locally
3. Set up Cognito authentication
4. Create IAM roles
5. Deploy to AgentCore Runtime
6. Test the remote deployment
7. Clean up resources

## ACME MCP Servers

In addition to the Rekognition example, this directory contains the production MCP servers used by the ACME chatbot:

| Server | Description | Tools |
|--------|-------------|-------|
| `aws-documentation-mcp-server/` | AWS documentation search | Search AWS docs, best practices |
| `aws-dataprocessing-mcp-server/` | Data analytics via Athena | SQL queries on telemetry data lake |
| `aws-mysql-mcp-server/` | Aurora MySQL CRM database | `run_query`, `get_table_schema` via RDS Data API |

The MySQL MCP server connects to Aurora MySQL Serverless v2 containing CRM data (customers, orders, products, support tickets) and exposes it through the MCP protocol.

## Project Structure

```
aws-mcp-server-agentcore/
├── mcp-agentcore-runtime.ipynb    # Main deployment notebook
├── requirements.txt               # Python dependencies
├── utils.py                      # Helper functions for Cognito and IAM
├── amazon-rekognition-mcp-server/ # MCP server implementation (example)
├── aws-documentation-mcp-server/  # AWS docs search MCP server
├── aws-dataprocessing-mcp-server/ # Athena data processing MCP server
├── aws-mysql-mcp-server/          # Aurora MySQL CRM MCP server
├── .env                          # Environment variables (create this)
├── .gitignore                    # Git ignore rules
└── README.md                     # This file

# Auto-generated files (excluded from git):
├── mcp-server.py                 # FastMCP wrapper for deployment
├── mcp-client.py                 # Local test client
├── mcp_client_remote.py          # Remote test client
├── Dockerfile                    # Container configuration
└── .bedrock_agentcore.yaml       # AgentCore configuration
```

## Architecture

### Local Development
```
[MCP Server] ←→ [Local Client] ←→ [Amazon Rekognition API]
```

### Production Deployment
```
[Remote Client] ←→ [HTTPS/JWT] ←→ [AgentCore Runtime] ←→ [Container] ←→ [MCP Server] ←→ [Amazon Rekognition API]
```

## Key Components

### FastMCP Wrapper (`mcp-server.py`)
Converts the stdio-based AWS MCP server to HTTP transport for AgentCore compatibility:
- Imports all 8 Rekognition tools
- Configures HTTP server on port 8000
- Enables stateless operation
- Provides proper MCP protocol implementation

### Authentication System
- **Amazon Cognito**: Provides JWT tokens for secure access
- **Bearer Token**: Used for HTTPS authentication
- **IAM Roles**: Proper permissions for AgentCore execution

### Testing Clients
- **Local Client**: Tests server functionality during development
- **Remote Client**: Validates deployed server with full authentication

## Usage Examples

### Local Testing
```bash
# Terminal 1: Start MCP server
python mcp-server.py

# Terminal 2: Test connectivity
python mcp-client.py
```

### Remote Testing
```bash
# Test deployed server
python mcp_client_remote.py
```

### Tool Usage
Once deployed, the MCP server exposes tools that can be called via the MCP protocol:
```python
# Example: Detect labels in an image
{
    "tool": "detect_labels",
    "arguments": {
        "image_path": "/path/to/image.jpg"
    }
}
```

## Deployment Process

The notebook automates the complete deployment pipeline:

1. **Preparation**: Install dependencies and validate prerequisites
2. **Local Testing**: Verify MCP server functionality
3. **Authentication Setup**: Configure Cognito for JWT authentication
4. **IAM Configuration**: Create execution roles with proper permissions
5. **Runtime Configuration**: Set up AgentCore deployment parameters
6. **Container Deployment**: Build and push Docker images to ECR
7. **Service Deployment**: Deploy to AgentCore Runtime
8. **Status Monitoring**: Wait for deployment completion
9. **Configuration Storage**: Store credentials for remote access
10. **Remote Testing**: Validate deployed service
11. **Cleanup**: Remove all created resources

## Security Considerations

- **Authentication**: JWT-based authentication via Amazon Cognito
- **Authorization**: IAM roles with least-privilege permissions
- **Transport**: HTTPS encryption for all communications
- **Secrets Management**: AWS Secrets Manager for credential storage
- **Network Security**: AgentCore Runtime provides secure execution environment

## Troubleshooting

### Common Issues
- **Authentication Failures**: Verify Cognito configuration and bearer tokens
- **Permission Errors**: Check IAM role permissions for Rekognition access
- **Deployment Failures**: Ensure Docker is running and ECR permissions are correct
- **Connection Issues**: Verify AgentCore Runtime status is "READY"

### Debugging
- Check CloudWatch logs for runtime errors
- Verify AWS credentials and permissions
- Test local server before remote deployment
- Validate environment variables in `.env` file

## Contributing

This project serves as a template for deploying AWS MCP servers to AgentCore Runtime. Contributions are welcome for:
- Additional AWS service MCP servers
- Improved error handling and logging
- Enhanced security configurations
- Documentation improvements

## License

This project is licensed under the Apache License 2.0. See the AWS MCP repository for detailed license information.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review AWS documentation for Bedrock AgentCore
- Consult the AWS MCP repository for server-specific issues
- Open issues in this repository for deployment-related problems
