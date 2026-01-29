# MCP Registry Stack

A serverless application for browsing and managing MCP (Model Context Protocol) servers deployed on AWS Bedrock AgentCore.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│   CloudFront CDN                                            │
│   ├─ /*        → S3 (React SPA)                             │
│   └─ /api/*    → API Gateway                                │
└─────────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
   ┌─────────────────┐         ┌─────────────────┐
   │  S3 Bucket      │         │  API Gateway    │
   │  (React App)    │         │  + Cognito Auth │
   └─────────────────┘         └────────┬────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │  Lambda (Node.js)│
                               └────────┬────────┘
                                        │
                      ┌─────────────────┼─────────────────┐
                      ▼                 ▼                 ▼
              ┌─────────────┐   ┌─────────────┐   ┌───────────┐
              │  DynamoDB   │   │  AgentCore  │   │  Secrets  │
              │  (registry) │   │  (MCP APIs) │   │  Manager  │
              └─────────────┘   └─────────────┘   └───────────┘
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Node.js** 18+ and npm
3. **AWS CDK** CLI installed (`npm install -g aws-cdk`)
4. **Agent Stack deployed** - This stack imports Cognito and MCP server ARNs from the agent-stack

Verify agent-stack exports exist:
```bash
aws cloudformation list-exports --query "Exports[?starts_with(Name, 'Acme')].Name" --output table
```

Required exports:
- `AcmeUserPoolId`
- `AcmeFrontendClientId`
- `AcmeMcpCredentialsArn`
- `AcmeAwsDocsMcpArn`
- `AcmeDataprocMcpArn`
- `AcmeRekognitionMcpArn`
- `AcmeNovaCanvasMcpArn`

## Installation

### 1. Install CDK dependencies

```bash
cd mcpregistry-stack
npm install
```

### 2. Install Lambda dependencies

```bash
cd lambda
npm install
cd ..
```

### 3. Install Frontend dependencies

```bash
cd frontend/mcp-registry
npm install
cd ../..
```

## Configuration

### Frontend Environment Variables

Create `.env` file in `frontend/mcp-registry/`:

```bash
cp frontend/mcp-registry/.env.example frontend/mcp-registry/.env
```

Edit `.env` with values from agent-stack outputs:

```bash
# Get values from agent-stack
aws cloudformation describe-stacks --stack-name AcmeAgentCoreStack \
  --query "Stacks[0].Outputs[?contains(OutputKey, 'UserPoolId') || contains(OutputKey, 'ClientId')]" \
  --output table
```

Update `.env`:
```
VITE_COGNITO_USER_POOL_ID=us-west-2_XXXXXXXXX
VITE_COGNITO_APP_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
VITE_AWS_REGION=us-west-2
```

### 4. Build Frontend

```bash
cd frontend/mcp-registry
npm run build
cd ../..
```

## Deploy

### First-time deployment

```bash
# Bootstrap CDK (if not done before)
npx cdk bootstrap

# Deploy the stack
npx cdk deploy
```

### Subsequent deployments

```bash
# Rebuild frontend if changed
cd frontend/mcp-registry && npm run build && cd ../..

# Deploy
npx cdk deploy
```

## Stack Outputs

After deployment, note these outputs:

| Output | Description |
|--------|-------------|
| `FrontendFrontendUrlE3736ECE` | CloudFront URL for the frontend |
| `ApiApiUrlF2D81078` | API Gateway endpoint |
| `UserPoolId` | Cognito User Pool (from agent-stack) |
| `FrontendClientId` | Cognito App Client (from agent-stack) |
| `TableName` | DynamoDB table name |

## User Setup

The stack uses the same Cognito User Pool as agent-stack. Use existing users or create new ones:

```bash
# Create a new user
aws cognito-idp admin-create-user \
  --user-pool-id <UserPoolId> \
  --username user@example.com \
  --user-attributes Name=email,Value=user@example.com \
  --temporary-password TempPass123! \
  --region us-west-2

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id <UserPoolId> \
  --username user@example.com \
  --password YourSecurePassword123! \
  --permanent \
  --region us-west-2
```

## Usage

1. Open the CloudFront URL from stack outputs
2. Login with Cognito credentials
3. Browse pre-seeded MCP servers (AWS Docs, Data Processing, Rekognition, Nova Canvas)
4. Click on a server to view details
5. Click "Refresh Tools" to fetch tools from the MCP server
6. Use "Register Server" to add new MCP servers

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/servers | List all servers |
| GET | /api/servers/{id} | Get server details |
| POST | /api/servers | Register new server |
| PUT | /api/servers/{id} | Update server |
| DELETE | /api/servers/{id} | Delete server |
| GET | /api/servers/{id}/tools | Get cached tools |
| GET | /api/servers/{id}/tools?refresh=true | Force refresh tools from MCP server |

## Troubleshooting

### Login fails
- Verify Cognito User Pool ID and Client ID in `.env`
- Ensure user exists and password is set (not temporary)
- Check browser console for errors

### Tools not loading (empty response)
- Check Lambda logs: `aws logs tail /aws/lambda/mcp-registry-get-tools --since 10m`
- Verify MCP credentials secret exists: `aws secretsmanager get-secret-value --secret-id acme-chatbot/mcp-credentials`
- Common errors:
  - `406`: Accept header issue (should include `text/event-stream`)
  - `401 client_id mismatch`: Using wrong Cognito client
  - `403 Authorization method mismatch`: Need OAuth token, not SigV4

### API returns 401 Unauthorized
- Ensure frontend sends ID token (not access token) in Authorization header
- Check token expiration

### CloudFront returns 403
- Wait for CloudFront distribution to deploy (can take 10-15 minutes)
- Invalidate cache: `aws cloudfront create-invalidation --distribution-id <id> --paths "/*"`

## Development

### Local frontend development

```bash
cd frontend/mcp-registry
npm run dev
```

Note: API calls will fail locally unless you configure a proxy to the deployed API Gateway.

### Lambda testing

Test individual Lambda functions via AWS Console or CLI:

```bash
aws lambda invoke \
  --function-name mcp-registry-list-servers \
  --payload '{}' \
  response.json
```

## Cleanup

```bash
npx cdk destroy
```

Note: This will delete all resources including the DynamoDB table with server data.
