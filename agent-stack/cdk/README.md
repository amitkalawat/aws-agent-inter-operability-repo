# ACME Corp Bedrock AgentCore CDK Stack

This CDK stack deploys the complete ACME Corp chatbot infrastructure on AWS, including authentication, frontend, backend agent, and MCP servers.

## Deployment

> **For deployment instructions, see the [main README](../../README.md) in the repository root.**
>
> The main README contains the complete step-by-step deployment guide with verification checks.

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

## Configuration

Configuration is managed in `lib/config/index.ts`:

| Variable | Default | Description |
|----------|---------|-------------|
| `aws.region` | `us-west-2` | AWS deployment region |
| `agent.runtimeName` | `acme_chatbot` | Main agent runtime name |
| `agent.model` | `anthropic.claude-haiku-4-5-20250414-v1:0` | Bedrock model ID (Claude Haiku 4.5) |
| `cognito.userPoolName` | `acme-corp-agentcore-users` | Cognito User Pool name |

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

## Project Structure

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

## Development Commands

```bash
# Synthesize CloudFormation template
cdk synth

# Compare deployed stack with current state
cdk diff

# Deploy stack
cdk deploy AcmeAgentCoreStack

# Destroy stack
cdk destroy AcmeAgentCoreStack

# List stacks
cdk list
```

## Viewing Logs

```bash
# Agent runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/acme_chatbot-* --region us-west-2 --follow

# MCP server logs
aws logs tail /aws/bedrock-agentcore/runtimes/aws_docs_mcp-* --region us-west-2 --follow
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `Cannot find asset at .../build` | Frontend not built | Build frontend first: `cd ../frontend/acme-chat && npm run build` |
| `CDK bootstrap required` | First deploy to account/region | Run `cdk bootstrap aws://ACCOUNT/us-west-2` |
| `Docker daemon is not running` | Docker not started | Start Docker Desktop |

### Cognito Authentication Issues

The frontend uses `USER_PASSWORD_AUTH` flow (not Hosted UI) which works reliably with admin-created users. If authentication fails:

```bash
# Test authentication via CLI
aws cognito-idp initiate-auth \
  --client-id <ClientId> \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters 'USERNAME=user1@test.com,PASSWORD=Abcd1234@' \
  --region us-west-2
```

### MCP Credentials Issues

The CDK stack automatically syncs Cognito client secrets to Secrets Manager on every deploy. If MCP initialization fails, redeploy the stack:

```bash
cdk deploy AcmeAgentCoreStack
```

### Debug Mode

Set `developmentMode: true` in `bin/app.ts` for:
- DESTROY removal policy (easy cleanup)
- Auto-delete S3 objects
- Detailed CloudFormation outputs

## Automated Safeguards

| Safeguard | Description |
|-----------|-------------|
| **MCP Secret Sync** | Custom Resource syncs Cognito client secret to Secrets Manager on every deploy |
| **5-min Secret Cache** | Agent re-fetches secrets from Secrets Manager every 5 minutes |
| **Auto-regenerate .env** | `deploy-frontend.sh` fetches fresh config from CloudFormation |

## Security Considerations

- Cognito User Pool uses email verification
- MCP client secret stored in Secrets Manager
- Frontend bucket has all public access blocked
- CloudFront uses HTTPS redirect
- Non-root user in Docker containers
- IAM policies follow least privilege principle

## License

MIT
