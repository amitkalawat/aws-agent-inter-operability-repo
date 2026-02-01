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

### 3. Build Frontend FIRST (Required)

> **Critical**: The CDK stack references the frontend `build/` directory for S3 deployment. You must build the frontend before running `cdk deploy` or the deployment will fail.

```bash
cd ../frontend/acme-chat
npm install
npm run build
cd ../../cdk
```

### 4. Deploy CDK Stack

```bash
cdk deploy AcmeAgentCoreStack
```

### 5. Deploy Frontend with Correct Config

After CDK deployment, use the deploy script to regenerate config from CloudFormation outputs and redeploy:

```bash
cd ../frontend/acme-chat
./scripts/deploy-frontend.sh
```

This script automatically:
- Fetches Cognito/Agent config from CloudFormation outputs
- Generates the `.env` file with correct values
- Rebuilds the React app
- Deploys to S3 and invalidates CloudFront cache

## Post-Deployment Steps

### 5. Create Admin User

The Cognito User Pool is configured with self-signup disabled for security. You must manually create users via AWS CLI:

```bash
# Create an admin user
aws cognito-idp admin-create-user \
  --user-pool-id <CognitoUserPoolId> \
  --username admin@acme.com \
  --user-attributes Name=email,Value=admin@acme.com Name=email_verified,Value=true \
  --temporary-password 'YourTempPassword123!' \
  --message-action SUPPRESS \
  --region us-west-2

# Example with actual User Pool ID from deployment output:
aws cognito-idp admin-create-user \
  --user-pool-id us-west-2_XXXXXXXXX \
  --username admin@acme.com \
  --user-attributes Name=email,Value=admin@acme.com Name=email_verified,Value=true \
  --temporary-password 'Acme@2024!' \
  --message-action SUPPRESS \
  --region us-west-2
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

**Note:** Users will be prompted to change their password on first login (status: `FORCE_CHANGE_PASSWORD`).

### 6. Set Permanent Password

Set a permanent password to skip the password change prompt on first login:

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id <CognitoUserPoolId> \
  --username admin@acme.com \
  --password 'YourPermanentPassword123!' \
  --permanent \
  --region us-west-2
```

This changes the user status from `FORCE_CHANGE_PASSWORD` to `CONFIRMED`.

### 7. Verify User Status

Confirm the user is ready to login:

```bash
aws cognito-idp admin-get-user \
  --user-pool-id <CognitoUserPoolId> \
  --username admin@acme.com \
  --region us-west-2 \
  --query 'UserStatus' \
  --output text

# Expected output: CONFIRMED
```

### 8. Update Frontend Configuration

After deployment, update the frontend configuration with the stack outputs (see [Frontend Configuration](#frontend-configuration) section below).

## Configuration

### Environment Variables

Configuration is managed in `lib/config/index.ts`:

| Variable | Default | Description |
|----------|---------|-------------|
| `aws.region` | `us-west-2` | AWS deployment region |
| `agent.runtimeName` | `acme_chatbot` | Main agent runtime name |
| `agent.model` | `anthropic.claude-haiku-4-5-20250414-v1:0` | Bedrock model ID (Claude Haiku 4.5) |
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

> **Note**: The issues below have been fixed in the codebase. This section documents the root causes and solutions for reference.

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

**Cognito Authentication: "Incorrect username or password" Error** ✅ FIXED

When using admin-created users (via `admin-create-user` and `admin-set-user-password`), the Cognito Hosted UI's SRP (Secure Remote Password) authentication flow doesn't work correctly because admin-created users don't have SRP verifiers properly initialized.

**Solution (already implemented):** The frontend uses direct Cognito API calls with `USER_PASSWORD_AUTH` flow instead of the Hosted UI:

```typescript
// In AuthService.ts - loginWithCredentials() method
const response = await fetch(
  `https://cognito-idp.${region}.amazonaws.com/`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-amz-json-1.1',
      'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
    },
    body: JSON.stringify({
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: clientId,
      AuthParameters: { USERNAME: email, PASSWORD: password },
    }),
  }
);
```

**Why this works:**
1. Bypasses Hosted UI completely (no SRP)
2. Cognito App Client has `ALLOW_USER_PASSWORD_AUTH` enabled (configured in CDK)
3. Works reliably with admin-created users

**Verifying:**
```bash
# Test authentication via AWS CLI (should return tokens)
aws cognito-idp initiate-auth \
  --client-id <ClientId> \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters 'USERNAME=user1@test.com,PASSWORD=Abcd1234@' \
  --region us-west-2
```

**MCP Client Initialization Failed / Invalid Client Secret** ✅ FIXED

This error occurs when the MCP credentials in Secrets Manager don't match the actual Cognito client secret. This can happen if:
- The Cognito client was recreated (gets new secret)
- The stack was updated but the secret wasn't synced

**Solution (already implemented):** The CDK stack includes a Custom Resource (`SecretsConstruct`) that automatically syncs the Cognito client secret to Secrets Manager on every deployment. The agent also has a 5-minute secret cache TTL to pick up new secrets quickly.

If you still encounter this issue (shouldn't happen with current implementation):

1. Redeploy the CDK stack to trigger the secret sync:
   ```bash
   cdk deploy AcmeAgentCoreStack
   ```

2. Verify the secret was synced:
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id acme-chatbot/mcp-credentials \
     --region us-west-2 \
     --query 'SecretString' --output text | jq .
   ```

3. The agent caches secrets for 5 minutes, so wait briefly or send a new request.

**Stale Frontend Configuration** ✅ FIXED

If the frontend uses outdated Cognito or Agent ARN values after stack recreation.

**Solution (already implemented):** The `deploy-frontend.sh` script auto-regenerates `.env` from CloudFormation outputs:
```bash
cd frontend/acme-chat
./scripts/deploy-frontend.sh
```

This script:
1. Fetches fresh values from CloudFormation outputs
2. Generates a new `.env` file
3. Rebuilds the frontend
4. Deploys to S3 and invalidates CloudFront cache

### Debug Mode

Set `developmentMode: true` in `bin/app.ts` for:
- DESTROY removal policy (easy cleanup)
- Auto-delete S3 objects
- Detailed CloudFormation outputs

## Deployment Best Practices

> **✅ Verified**: This workflow was tested with a full stack delete/recreate cycle and works correctly.

### After Stack Delete/Recreate

When you delete and recreate the stack, follow these steps:

1. **Deploy the CDK stack:**
   ```bash
   cd agent-stack/cdk
   cdk deploy AcmeAgentCoreStack
   ```

2. **Create test users** (User Pool is new, no users exist):
   ```bash
   # Get the new User Pool ID from stack outputs
   USER_POOL_ID=$(aws cloudformation describe-stacks \
     --stack-name AcmeAgentCoreStack \
     --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' \
     --output text --region us-west-2)

   # Create user
   aws cognito-idp admin-create-user \
     --user-pool-id $USER_POOL_ID \
     --username user1@test.com \
     --user-attributes Name=email,Value=user1@test.com Name=email_verified,Value=true \
     --message-action SUPPRESS \
     --region us-west-2

   # Set permanent password
   aws cognito-idp admin-set-user-password \
     --user-pool-id $USER_POOL_ID \
     --username user1@test.com \
     --password 'Abcd1234@' \
     --permanent \
     --region us-west-2
   ```

3. **Deploy the frontend** (gets fresh config from CloudFormation):
   ```bash
   cd ../frontend/acme-chat
   ./scripts/deploy-frontend.sh
   ```

4. **Verify deployment** (wait 1-2 min for CloudFront cache):
   ```bash
   # Test Cognito authentication
   CLIENT_ID=$(aws cloudformation describe-stacks \
     --stack-name AcmeAgentCoreStack \
     --query 'Stacks[0].Outputs[?OutputKey==`CognitoAppClientId`].OutputValue' \
     --output text --region us-west-2)

   aws cognito-idp initiate-auth \
     --client-id $CLIENT_ID \
     --auth-flow USER_PASSWORD_AUTH \
     --auth-parameters 'USERNAME=user1@test.com,PASSWORD=Abcd1234@' \
     --region us-west-2 \
     --query 'AuthenticationResult.AccessToken' \
     --output text | head -c 20 && echo "... ✓ Auth working"
   ```

5. **Test the application**:
   - Open the CloudFront URL from stack outputs
   - Login with `user1@test.com` / `Abcd1234@`
   - Send a chat message to verify agent connectivity

### What's Automated vs Manual

| Step | Automated? | Notes |
|------|------------|-------|
| MCP secret sync to Secrets Manager | ✅ Yes | Custom Resource runs on every CDK deploy |
| Frontend .env generation | ✅ Yes | `deploy-frontend.sh` fetches from CloudFormation |
| Frontend build & S3 upload | ✅ Yes | Part of `deploy-frontend.sh` |
| CloudFront cache invalidation | ✅ Yes | Part of `deploy-frontend.sh` |
| Test user creation | ❌ Manual | Required once per new User Pool |
| Running `deploy-frontend.sh` | ❌ Manual | Run after CDK deploy |

### Automated Safeguards

The stack includes these safeguards to prevent configuration drift:

| Safeguard | Description |
|-----------|-------------|
| **MCP Secret Sync** | Custom Resource syncs actual Cognito client secret to Secrets Manager on every CDK deploy |
| **5-min Secret Cache** | Agent re-fetches secrets from Secrets Manager every 5 minutes |
| **Auto-regenerate .env** | `deploy-frontend.sh` fetches fresh config from CloudFormation before building |
| **Config Validation** | Frontend logs warnings if required environment variables are missing |

### What Gets Synced Automatically

| On CDK Deploy | On Frontend Deploy |
|---------------|-------------------|
| Cognito client secret → Secrets Manager | User Pool ID → .env |
| Agent runtime updated | Client ID → .env |
| MCP servers updated | Agent ARN → .env |
| | Rebuilds with fresh config |

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
