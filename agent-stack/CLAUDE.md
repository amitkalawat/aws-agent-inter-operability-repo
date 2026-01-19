# ACME Corp Bedrock AgentCore Chatbot - Claude Memory

This file contains key deployment instructions and project information for Claude to reference in future sessions.

## Project Overview

ACME Corp Bedrock AgentCore chatbot with:
- **Frontend**: React TypeScript app with AWS Cognito authentication
- **Backend**: Python Strands agent with Claude 3.7 Sonnet
- **Memory**: AWS Bedrock AgentCore Memory for conversation persistence
- **Tools**: Calculator (SymPy) and Weather
- **Authentication**: Cognito JWT with discovery URL
- **Region**: eu-central-1

## Deployment Instructions

### Agent Deployment (Primary Method)

**IMPORTANT**: The deployment directory expects agent files to be copied locally before deployment.

```bash
# Step 1: Copy agent files to deployment directory
cd backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/memory_manager.py .
cp ../agent/requirements.txt .

# Step 2: Deploy the agent
source .venv/bin/activate
python deploy_agent_with_auth.py
```

This script:
- Uses `bedrock_agentcore_starter_toolkit.Runtime`
- Loads Cognito configuration from `../../infrastructure/cognito/cognito_config.json`
- Deploys with JWT authentication
- Saves deployment info to `deployment_info_auth.json`

**Note**: Always copy the latest agent files before deployment to ensure changes are included in the container build.

### Alternative Deployment (agentcore CLI)

```bash
# Step 1: Copy agent files to deployment directory
cd backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/memory_manager.py .
cp ../agent/requirements.txt .

# Step 2: Deploy using agentcore CLI
source .venv/bin/activate
agentcore launch --config .bedrock_agentcore.yaml
```

Available CLI commands:
- `agentcore status` - Check deployment status
- `agentcore invoke` - Test agent invocation
- `agentcore launch --local` - Run locally for testing

### V2 Agent Deployment (Fresh Instance)

For deploying a new `acme_chatbot_v2` instance:

```bash
# Step 1: Copy agent files to deployment directory
cd backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/memory_manager.py .
cp ../agent/requirements.txt .

# Step 2: Deploy to acme_chatbot_v2
source .venv/bin/activate
python deploy_agent_fresh.py
```

This script:
- Creates a fresh `acme_chatbot_v2` agent instance
- Uses the same Cognito configuration
- Saves deployment info to `deployment_info_v2.json`
- Provides the new agent ARN for frontend configuration

### Key Configuration Files

1. **`.bedrock_agentcore.yaml`** - Main agent configuration:
   - Agent ID: `strands_claude_getting_started_auth-nYQSK477I1`
   - ECR Repository: `241533163649.dkr.ecr.eu-central-1.amazonaws.com/bedrock-agentcore-strands_claude_getting_started_auth`
   - Execution Role: `AmazonBedrockAgentCoreSDKRuntime-eu-central-1-6deb7df49a`
   - Cognito Discovery URL: `https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_CF2vh6s7M/.well-known/openid-configuration`
   - App Client ID: `3cbhcr57gvuh4ffnv6sqlha5eo`

2. **`deployment_info_auth.json`** - Stores deployment details after successful deployment

3. **Agent files**:
   - Main agent: `backend/agent/strands_claude.py`
   - Memory manager: `backend/agent/memory_manager.py`
   - Requirements: `backend/agent/requirements.txt`

## Frontend Access

- **URL**: https://d3dh52mpp8dm84.cloudfront.net
- **Authentication**: Cognito user pool login required
- **Admin credentials**: Stored in Cognito configuration

## Memory Implementation ✅ FIXED

The agent uses AWS Bedrock AgentCore Memory for conversation persistence:
- **Memory Strategy**: Short-term memory (empty strategies list) following AWS documentation
- **Storage**: Events stored per sanitized user ID and session
- **Retrieval**: Recent conversation history from current session using `get_last_k_turns`
- **IAM Permissions**: ✅ Memory permissions applied via `memory-policy.json`
- **Session/Actor Extraction**: ✅ Parses `[META:...]` format from frontend prompts
- **Actor ID Sanitization**: ✅ Converts `admin@acme.com` → `admin_at_acme_dot_com` for AWS compliance

### Memory Features (v3.0)

✅ **Fixed Issues**:
- Memory ID format validation (AWS pattern: `{name}-{10chars}`)
- Actor ID sanitization for AWS pattern compliance
- Session/Actor extraction from embedded metadata
- Empty strategies list for short-term memory
- Proper memory retrieval from `list_memories()` API

### Memory IAM Policy

**File**: `backend/deployment/memory-policy.json`
**Apply Command**: 
```bash
cd backend/deployment
source .venv/bin/activate
python apply_memory_policy.py
```

**Required Permissions**:
- `bedrock-agentcore:CreateMemory`
- `bedrock-agentcore:ListMemories` 
- `bedrock-agentcore:CreateEvent`
- `bedrock-agentcore:GetLastKTurns`
- Additional logging permissions

### Memory Troubleshooting

If memory isn't working:
1. ✅ IAM permissions are now properly configured
2. ✅ Memory creation/reuse logic fixed in `memory_manager.py`
3. Check logs: `aws logs tail /aws/bedrock-agentcore/runtimes/strands_claude_getting_started_auth-nYQSK477I1-DEFAULT --region eu-central-1`
4. Test locally: `python test_memory_integration.py`

## Infrastructure

- **AWS Account**: 241533163649
- **Region**: eu-central-1
- **Cognito User Pool**: eu-central-1_CF2vh6s7M
- **CodeBuild Project**: bedrock-agentcore-strands_claude_getting_started_auth-builder
- **Platform**: linux/arm64

## Common Commands

### Full Deployment Workflow
```bash
# Copy latest agent files
cd backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/memory_manager.py .
cp ../agent/requirements.txt .

# Deploy
source .venv/bin/activate
python deploy_agent_with_auth.py
```

### Check deployment logs:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/strands_claude_getting_started_auth-nYQSK477I1-DEFAULT --region eu-central-1 --since 10m
```

### Update IAM policies:
```bash
aws iam put-role-policy --role-name AmazonBedrockAgentCoreSDKRuntime-eu-central-1-6deb7df49a --policy-name BedrockAgentCoreRuntimeExecutionPolicy-strands_claude_getting_started_auth --policy-document file://memory-policy-addition.json
```

### Test agent locally:
```bash
cd backend/agent
python strands_claude.py '{"prompt": "Hello, test message"}'
```

## Project Structure

```
├── backend/
│   ├── agent/                 # Agent source code
│   │   ├── strands_claude.py     # Main agent
│   │   ├── memory_manager.py     # Memory implementation
│   │   └── requirements.txt      # Python dependencies
│   └── deployment/            # Deployment scripts and config
│       ├── .bedrock_agentcore.yaml  # Main config
│       ├── deploy_agent_with_auth.py # Deployment script
│       └── deployment_info_auth.json # Deployment details
├── frontend/                  # React TypeScript app
└── infrastructure/            # AWS infrastructure
    └── cognito/              # Cognito setup
```

## Deployment File Structure

**IMPORTANT**: The deployment directory (`backend/deployment/`) expects all agent files to be copied locally before deployment. This is because the Docker build context only includes files in the deployment directory.

### Files to Copy Before Deployment:
- `../agent/strands_claude.py` → `./strands_claude.py` (Main agent)
- `../agent/memory_manager.py` → `./memory_manager.py` (Memory functionality) 
- `../agent/requirements.txt` → `./requirements.txt` (Python dependencies)

### Always Remember:
1. Copy files from `backend/agent/` to `backend/deployment/` before deploying
2. This ensures the latest code changes are included in the container build
3. The deployment script looks for files locally in the deployment directory

## Recent Changes

- ✅ **Added DataProcessing MCP Integration** - Agent now supports both AWS Documentation and DataProcessing MCPs
- ✅ **Dual MCP Support** - Nested context managers handle AWS docs + DataProcessing clients simultaneously
- ✅ **Bearer Token Authentication** - Uses same OAuth flow for both MCPs (no Accept headers)
- ✅ **Enhanced System Prompt** - Includes complete ACME Corp data schema and query templates
- ✅ **V2 Deployment Support** - Added `deploy_agent_fresh.py` for deploying `acme_chatbot_v2`
- Added AgentCore Memory functionality for conversation persistence
- Fixed memory manager to reuse existing memory resources instead of creating duplicates  
- Updated IAM permissions to include AgentCore Memory actions
- Implemented proper event storage and retrieval for conversation history
- Fixed memory manager error handling to properly handle "already exists" scenarios
- Added deployment file copying instructions to prevent missing code updates
- Enhanced schema documentation in system prompt to prevent query trial-and-error issues

## DataProcessing MCP Integration ✅ IMPLEMENTED

The agent now supports dual MCP integration:

### Available MCPs
- **AWS Documentation MCP**: Search AWS documentation, best practices, configuration guides
- **DataProcessing MCP**: Query and analyze ACME Corp's real-time streaming data using Athena SQL

### Configuration
- **Secrets Manager**: `MCP_DATAPROC_URL` configured with runtime `dataproc_mcp_ibcv3-vwsZvUBHMP`
- **Authentication**: Same Bearer token OAuth flow for both MCPs
- **Headers**: `Authorization: Bearer {token}` only (no Accept headers)

### Features
- **Intelligent Client Management**: Adapts to available MCPs (both, single, or fallback)
- **ACME Data Schema**: Complete documentation of streaming data tables and query templates
- **Nested Context Managers**: Proper resource management for multiple MCP clients
- **Real-time Data Access**: Query acme_telemetry and acme_streaming_data databases

## Data Query Improvements

### Enhanced Schema Documentation (Implemented)
Added detailed data type and value hints to the system prompt to prevent query errors:
- **Data Types**: Specified that `event_timestamp` is VARCHAR requiring `CAST(event_timestamp AS timestamp)`
- **Value Examples**: Added actual enum values (`event_type`: 'start', 'pause', 'resume', 'stop', 'complete'; `title_type`: 'movie', 'series', 'documentary')
- **Query Templates**: Provided common query patterns for real-time data analysis

### Future Infrastructure Improvements (Technical Debt)
Consider these AWS Glue catalog improvements for better query performance:

1. **Data Type Corrections**:
   - Convert `event_timestamp` from VARCHAR to TIMESTAMP type
   - Convert other timestamp fields to proper TIMESTAMP types
   - This would eliminate need for CAST operations in every query

2. **Data Standardization**:
   - Standardize enum values (consider uppercase for consistency)
   - Add CHECK constraints where appropriate
   - Add column comments in Glue catalog with valid value ranges

3. **Performance Optimizations**:
   - Partition tables by date for better query performance
   - Consider columnar formats (Parquet) with compression
   - Add indexes on frequently queried columns

**Impact**: These changes would reduce query complexity and improve performance, but require coordination with data pipeline team and testing of existing dependencies.

## Frontend-Backend Connection

### Frontend Configuration
The React frontend connects to the backend agent through:

**Configuration File**: `frontend/acme-chat/src/config.ts`
```typescript
agentcore: {
  agentArn: 'arn:aws:bedrock-agentcore:eu-central-1:241533163649:runtime/strands_claude_getting_started_auth-nYQSK477I1',
  region: 'eu-central-1',
  endpoint: 'https://bedrock-agentcore.eu-central-1.amazonaws.com'
}
```

**Service Implementation**: `frontend/acme-chat/src/services/AgentCoreService.ts`
- Constructs API URLs by combining endpoint + URL-encoded agent ARN
- Final URL format: `https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/[ENCODED_ARN]/invocations?qualifier=DEFAULT`
- Supports both regular and streaming requests
- Handles authentication via Bearer tokens and session management

### API Request Flow
1. **Authentication**: Uses Cognito JWT tokens in Authorization header
2. **Session Management**: Generates unique session IDs for conversation persistence
3. **Metadata Embedding**: Embeds session and user metadata in prompt format: `[META:{"sid":"session-id","uid":"user"}]actual_message`
4. **Request Types**:
   - Regular: POST to `/invocations?qualifier=DEFAULT`
   - Streaming: POST to `/invocations?qualifier=DEFAULT&streaming=true`

### Connection Configuration
- **Agent ARN**: Must match the deployed backend agent ARN exactly
- **Endpoint**: AWS Bedrock AgentCore regional endpoint
- **Region**: Must be consistent across all configurations (currently `eu-central-1`)
- **Authentication**: Cognito User Pool integration with JWT discovery URL

### Updating Agent ARN
When deploying a new agent version, the `agentArn` in `config.ts` must be updated to match the new deployment ARN. The current configuration is already pointing to the correct agent:
`strands_claude_getting_started_auth-nYQSK477I1`