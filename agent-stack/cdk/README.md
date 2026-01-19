# ACME Corp Bedrock AgentCore CDK Stack

This CDK stack deploys the complete ACME Corp chatbot infrastructure on AWS, including authentication, frontend, backend agent, and MCP servers.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AcmeAgentCoreStack (CDK)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │   Frontend      │    │         Backend                   │   │
│  │  ┌───────────┐  │    │  ┌────────────────────────────┐  │   │
│  │  │ S3 Bucket │  │    │  │  Main Agent Runtime        │  │   │
│  │  └─────┬─────┘  │    │  │  (acme_chatbot)            │  │   │
│  │        │        │    │  │  - Strands + Haiku 4.5     │  │   │
│  │  ┌─────▼─────┐  │    │  │  - Memory integration      │  │   │
│  │  │CloudFront │  │    │  └────────────────────────────┘  │   │
│  │  └───────────┘  │    │                                   │   │
│  └─────────────────┘    │  ┌────────────────────────────┐  │   │
│                         │  │  MCP Servers (Runtimes)    │   │   │
│  ┌─────────────────┐    │  │  - AWS Documentation       │   │   │
│  │   Auth Layer    │    │  │  - DataProcessing          │   │   │
│  │  ┌───────────┐  │    │  │  - Rekognition             │   │   │
│  │  │ Cognito   │  │    │  │  - Nova Canvas             │   │   │
│  │  │ User Pool │  │    │  └────────────────────────────┘  │   │
│  │  └───────────┘  │    │                                   │   │
│  └─────────────────┘    │  ┌────────────────────────────┐  │   │
│                         │  │  AgentCore Memory          │   │   │
│  ┌─────────────────┐    │  └────────────────────────────┘  │   │
│  │ Secrets Manager │    └──────────────────────────────────┘   │
│  │ (MCP creds)     │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Authentication (Cognito)
- User Pool for email-based authentication
- Frontend client (public, no secret) for React app
- MCP client (confidential, with secret) for M2M auth
- Password policy: 8+ chars, uppercase, lowercase, numbers, symbols

### Backend Agent
- Strands agent with Claude Haiku 4.5 model
- AgentCore Memory for conversation persistence
- Code interpreter for data visualization
- Multiple MCP client integrations

### MCP Servers
1. **AWS Documentation** - Search AWS docs, best practices, configuration guides
2. **DataProcessing** - Athena, Glue, EMR data processing
3. **Rekognition** - Image analysis and recognition
4. **Nova Canvas** - Image generation

### Frontend
- React TypeScript application
- S3 bucket with CloudFront distribution
- SPA routing configuration
- Optimized caching for static assets

### Secrets Manager
- MCP credentials storage
- Auto-generated client secrets
- Secure access for agent runtime

## Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js 18+ and npm
- Docker (for building container images)
- AWS CDK CLI (`npm install -g aws-cdk`)

## Quick Start

### 1. Install Dependencies

```bash
cd agent-stack/cdk
npm install
```

### 2. Bootstrap CDK (First Time Only)

```bash
cdk bootstrap
```

### 3. Build Frontend

Before deploying, build the React frontend:

```bash
cd ../frontend/acme-chat
npm install
npm run build
cd ../../cdk
```

### 4. Deploy Stack

```bash
cdk deploy
```

## Configuration

### Environment Variables

Configuration is managed in `lib/config/index.ts`:

| Variable | Default | Description |
|----------|---------|-------------|
| `aws.region` | `us-west-2` | AWS deployment region |
| `agent.runtimeName` | `acme_chatbot` | Main agent runtime name |
| `agent.model` | `anthropic.claude-3-5-haiku-20241022-v1:0` | Bedrock model ID |
| `cognito.userPoolName` | `acme-corp-agentcore-users` | Cognito User Pool name |

### Modifying Configuration

Edit `lib/config/index.ts` to customize:
- AWS region
- Naming conventions
- Model selection
- Token validity periods
- Cache policies

## Stack Outputs

After deployment, the following outputs are available:

| Output | Description |
|--------|-------------|
| `FrontendUrl` | CloudFront distribution URL |
| `AgentArn` | Main agent runtime ARN |
| `CognitoUserPoolId` | Cognito User Pool ID |
| `CognitoAppClientId` | Frontend app client ID |
| `DiscoveryUrl` | OIDC discovery URL for JWT validation |
| `MemoryId` | AgentCore Memory resource ID |

## Frontend Configuration

After deployment, update the frontend configuration with the stack outputs:

```typescript
// frontend/acme-chat/src/config.ts
export const config = {
  cognito: {
    userPoolId: '<CognitoUserPoolId>',
    clientId: '<CognitoAppClientId>',
    region: 'us-west-2',
  },
  agentcore: {
    agentArn: '<AgentArn>',
    region: 'us-west-2',
    endpoint: 'https://bedrock-agentcore.us-west-2.amazonaws.com'
  }
};
```

## Development

### Project Structure

```
cdk/
├── bin/
│   └── app.ts                    # CDK app entry point
├── lib/
│   ├── acme-stack.ts             # Main stack
│   ├── constructs/
│   │   ├── cognito-construct.ts  # Cognito User Pool
│   │   ├── frontend-construct.ts # S3 + CloudFront
│   │   ├── agent-runtime-construct.ts  # Main agent
│   │   ├── mcp-server-construct.ts     # MCP servers
│   │   ├── memory-construct.ts   # AgentCore Memory
│   │   └── secrets-construct.ts  # Secrets Manager
│   └── config/
│       └── index.ts              # Configuration constants
├── docker/
│   ├── agent/                    # Main agent Dockerfile
│   └── mcp-servers/              # MCP server Dockerfiles
│       ├── aws-docs/
│       ├── dataproc/
│       ├── rekognition/
│       └── nova-canvas/
├── package.json
├── tsconfig.json
└── cdk.json
```

### Useful Commands

```bash
# Synthesize CloudFormation template
cdk synth

# Compare deployed stack with current state
cdk diff

# Deploy stack
cdk deploy

# Deploy with approval prompts disabled
cdk deploy --require-approval never

# Destroy stack
cdk destroy

# List stacks
cdk list
```

### Viewing Logs

```bash
# Agent runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/acme_chatbot-* --region us-west-2 --follow

# MCP server logs
aws logs tail /aws/bedrock-agentcore/runtimes/aws_docs_mcp-* --region us-west-2 --follow
```

## Testing

### Test Frontend Access

1. Navigate to the CloudFront URL from stack outputs
2. Log in with Cognito credentials
3. Send a chat message

### Test Agent Invocation

```bash
# Get JWT token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id <UserPoolId> \
  --client-id <ClientId> \
  --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=<email>,PASSWORD=<password> \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Invoke agent
curl -X POST \
  "https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/<AgentArn>/invocations?qualifier=DEFAULT" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how can you help me?"}'
```

## Troubleshooting

### Common Issues

**CDK Bootstrap Error**
```bash
# Ensure your AWS credentials are configured
aws sts get-caller-identity

# Bootstrap with explicit account and region
cdk bootstrap aws://<ACCOUNT_ID>/us-west-2
```

**Frontend Build Not Found**
```bash
# Ensure frontend is built before deployment
cd ../frontend/acme-chat && npm run build
```

**Permission Denied**
- Ensure IAM user/role has sufficient permissions
- Check CloudWatch Logs for detailed error messages

### Debug Mode

Set `developmentMode: true` in `bin/app.ts` for:
- DESTROY removal policy (easy cleanup)
- Auto-delete S3 objects
- Detailed CloudFormation outputs

## Security Considerations

- Cognito User Pool uses email verification
- MCP client secret stored in Secrets Manager
- Frontend bucket has all public access blocked
- CloudFront uses HTTPS redirect
- Non-root user in Docker containers
- IAM policies follow least privilege principle

## Cost Optimization

- CloudFront uses PRICE_CLASS_100 (North America/Europe)
- Development mode enables auto-cleanup
- Memory expiration set to 90 days
- Token caching reduces API calls

## License

MIT
