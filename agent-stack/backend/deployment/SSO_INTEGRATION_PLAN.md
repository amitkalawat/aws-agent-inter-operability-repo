# SSO Integration Plan - Consolidate to MCP Registry Cognito Pool

## Overview
This document outlines the plan to consolidate authentication across all ACME Corp applications using the MCP Registry Cognito pool in Frankfurt (eu-central-1) to enable Single Sign-On (SSO).

## Current State Analysis

### Three Separate Cognito Pools
1. **Agent Interoperability Demo** - `eu-central-1_CF2vh6s7M` (current app user authentication)
2. **Video Telemetry Dashboard** - Separate Cognito pool (linked from app)
3. **MCP Registry** - `eu-central-1_PaVtjk8dt` (target SSO pool in Frankfurt)

### MCP Registry Pool Details (Frankfurt)
- **Pool ID:** `eu-central-1_PaVtjk8dt`
- **Pool Name:** `mcp-registry-users-mcp-gateway-registry`
- **Domain:** `mcp-registry-241533163649-mcp-gateway-registry`
- **Existing Web Client:** `18n5b3rh0t0gb58pq7kb446pmi`
- **M2M Client:** `4rit5a00iqft9ak8sl5hb28sr` (for backend services)
- **Current Users:** 
  - `admin@example.com` (confirmed status)
  - One user pending password change

### Important Clarification
- **Backend agents are already using MCP Registry Cognito** for MCP service authentication (machine-to-machine)
- **Only frontend user authentication needs to be migrated** to the MCP Registry pool
- The backend MCP authentication flow (client credentials) remains unchanged

## Implementation Plan (Frontend-Focused)

### Phase 1: User Creation in MCP Registry Pool

Create user accounts in MCP Registry Cognito pool (`eu-central-1_PaVtjk8dt`):

```bash
# Create admin user for Agent Interoperability Demo
aws cognito-idp admin-create-user \
  --user-pool-id eu-central-1_PaVtjk8dt \
  --username admin@acmecorp.com \
  --user-attributes Name=email,Value=admin@acmecorp.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --region eu-central-1

# Optional: Create separate telemetry user if needed
aws cognito-idp admin-create-user \
  --user-pool-id eu-central-1_PaVtjk8dt \
  --username telemetry@acmecorp.com \
  --user-attributes Name=email,Value=telemetry@acmecorp.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --region eu-central-1
```

### Phase 2: Configure App Client for Frontend

#### Option A: Use Existing Web Client
Update the existing `mcp-registry-web-client` to include our frontend URLs:

```bash
aws cognito-idp update-user-pool-client \
  --user-pool-id eu-central-1_PaVtjk8dt \
  --client-id 18n5b3rh0t0gb58pq7kb446pmi \
  --explicit-auth-flows ALLOW_ADMIN_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_USER_SRP_AUTH \
  --callback-urls \
    "https://d1zugwkd4hiwal.cloudfront.net/auth/callback" \
    "https://d1zugwkd4hiwal.cloudfront.net/auth/oauth2/callback/cognito" \
    "https://d1zugwkd4hiwal.cloudfront.net/login" \
    "https://d3dh52mpp8dm84.cloudfront.net/callback" \
    "https://d22um2piuwyb63.cloudfront.net/callback" \
  --logout-urls \
    "https://d1zugwkd4hiwal.cloudfront.net/" \
    "https://d1zugwkd4hiwal.cloudfront.net/login" \
    "https://d3dh52mpp8dm84.cloudfront.net/" \
    "https://d22um2piuwyb63.cloudfront.net/" \
  --region eu-central-1
```

#### Option B: Create New Dedicated App Client
Create a separate client for the Agent Interoperability Demo:

```bash
aws cognito-idp create-user-pool-client \
  --user-pool-id eu-central-1_PaVtjk8dt \
  --client-name "agent-interop-demo-client" \
  --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_USER_PASSWORD_AUTH \
  --callback-urls "https://d3dh52mpp8dm84.cloudfront.net/callback" \
  --logout-urls "https://d3dh52mpp8dm84.cloudfront.net/" \
  --supported-identity-providers COGNITO \
  --region eu-central-1
```

Save the returned Client ID for the next steps.

### Phase 3: Update Frontend Configuration Files

#### 1. Update `frontend/acme-chat/src/config.ts`

```typescript
// Configuration for ACME Corp AgentCore Chat Application
export const config = {
  // AWS Cognito Configuration - Using MCP Registry Pool for SSO
  cognito: {
    userPoolId: 'eu-central-1_PaVtjk8dt',  // MCP Registry pool
    appClientId: '18n5b3rh0t0gb58pq7kb446pmi',  // Or new client ID from Phase 2
    region: 'eu-central-1',
    discoveryUrl: 'https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_PaVtjk8dt/.well-known/openid-configuration'
  },
  
  // AgentCore Configuration (unchanged)
  agentcore: {
    agentArn: 'arn:aws:bedrock-agentcore:eu-central-1:241533163649:runtime/strands_claude_getting_started_auth-nYQSK477I1',
    region: 'eu-central-1',
    endpoint: 'https://bedrock-agentcore.eu-central-1.amazonaws.com'
  },
  
  // Demo User Credentials (update after first login)
  demo: {
    username: 'admin@acmecorp.com',
    password: 'UPDATE_AFTER_FIRST_LOGIN'
  }
};
```

#### 2. Update `infrastructure/cognito/cognito_config.json`

```json
{
  "user_pool_id": "eu-central-1_PaVtjk8dt",
  "app_client_id": "18n5b3rh0t0gb58pq7kb446pmi",
  "region": "eu-central-1",
  "discovery_url": "https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_PaVtjk8dt/.well-known/openid-configuration",
  "admin_user": {
    "username": "admin@acmecorp.com",
    "password": "UPDATE_AFTER_FIRST_LOGIN"
  },
  "created_at": "2025-08-25 UPDATE",
  "notes": "Migrated to MCP Registry Cognito pool for SSO"
}
```

### Phase 4: Update Backend JWT Validation

#### Update `.bedrock_agentcore.yaml`

```yaml
authorizer_configuration:
  customJWTAuthorizer:
    discoveryUrl: https://cognito-idp.eu-central-1.amazonaws.com/eu-central-1_PaVtjk8dt/.well-known/openid-configuration
    allowedClients:
    - 18n5b3rh0t0gb58pq7kb446pmi  # Or new client ID
```

### Phase 5: Redeploy Agent with Updated Configuration

```bash
# Copy agent files to deployment directory
cd backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/memory_manager.py .
cp ../agent/requirements.txt .

# Deploy with updated auth configuration
source .venv/bin/activate
python deploy_agent_with_auth.py
```

## What Remains Unchanged

- ✅ **Backend MCP authentication** - Already using MCP Registry Cognito with client credentials
- ✅ **MCP service connections** - Continue working with existing m2m client
- ✅ **Secrets Manager configuration** - MCP credentials remain the same
- ✅ **Agent core logic** - No changes to agent functionality

## Benefits of Consolidation

1. **True Single Sign-On (SSO):** One login works across all applications:
   - Agent Interoperability Demo
   - Video Telemetry Dashboard
   - MCP Registry

2. **Centralized User Management:** All users managed in one Cognito pool in Frankfurt

3. **Simplified Authentication:** Consistent auth flow across all applications

4. **Better Security:** Single point for access control and audit logging

5. **Reduced Complexity:** Fewer Cognito pools to manage and maintain

## Testing Plan

### 1. User Creation and Password Setup
```bash
# Verify user was created
aws cognito-idp admin-get-user \
  --user-pool-id eu-central-1_PaVtjk8dt \
  --username admin@acmecorp.com \
  --region eu-central-1
```

### 2. Test Frontend Login
1. Update frontend configuration files
2. Build and deploy frontend:
   ```bash
   cd frontend/acme-chat
   npm run build
   cd ../infrastructure
   npm run deploy
   ```
3. Navigate to https://d3dh52mpp8dm84.cloudfront.net
4. Login with new credentials
5. Change password on first login

### 3. Verify SSO Functionality
1. Login to Agent Interoperability Demo
2. Click "Video Telemetry Dashboard" - should not require re-login
3. Click "MCP Registry" - should not require re-login
4. Verify all three applications recognize the same session

### 4. Validate Backend Services
1. Test agent invocation with new JWT token
2. Verify MCP services still authenticate correctly
3. Check memory persistence works
4. Validate data queries and visualizations

## Rollback Plan

If issues occur, revert configuration files:

1. Restore original `config.ts` with pool ID `eu-central-1_CF2vh6s7M`
2. Restore original `cognito_config.json`
3. Restore original `.bedrock_agentcore.yaml`
4. Redeploy agent with original configuration

## Security Considerations

1. **Password Policy:** Ensure strong password requirements in MCP Registry pool
2. **MFA:** Consider enabling MFA for additional security
3. **Token Expiration:** Configure appropriate token lifetimes for SSO
4. **CORS:** Ensure proper CORS configuration for cross-domain authentication
5. **Audit Logging:** Enable CloudTrail logging for authentication events

## Support and Troubleshooting

### Common Issues and Solutions

1. **Login fails with "User does not exist"**
   - Verify user was created in correct pool
   - Check username format (email vs username)

2. **"Invalid client ID" error**
   - Ensure app client ID is correctly updated in all config files
   - Verify client exists in the pool

3. **SSO not working between apps**
   - Check callback URLs are properly configured
   - Verify same Cognito domain is used
   - Ensure cookies are enabled and not blocked

4. **Backend authentication fails**
   - Verify JWT discovery URL is updated
   - Check allowed client IDs in agent configuration
   - Ensure agent was redeployed with new config

## Appendix: Current Infrastructure URLs

- **Agent Interoperability Demo:** https://d3dh52mpp8dm84.cloudfront.net
- **Video Telemetry Dashboard:** https://d22um2piuwyb63.cloudfront.net
- **MCP Registry:** https://d1zugwkd4hiwal.cloudfront.net

## Next Steps

1. [ ] Create users in MCP Registry Cognito pool
2. [ ] Configure app client with all callback URLs
3. [ ] Update frontend configuration files
4. [ ] Update backend JWT validation configuration
5. [ ] Redeploy agent with new configuration
6. [ ] Test SSO across all applications
7. [ ] Update documentation and inform team

---

**Document Version:** 1.0  
**Last Updated:** 2025-08-25  
**Author:** ACME Corp DevOps Team