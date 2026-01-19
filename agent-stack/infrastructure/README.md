# Infrastructure - AWS Resources

This directory will contain AWS infrastructure configuration for connecting the React frontend to the AgentCore backend.

## Planned Components

### Lambda Functions
- `lambda/agentcore_proxy.py` - Proxy function to call AgentCore from API Gateway

### CloudFormation/SAM Templates
- `cloudformation/template.yaml` - Infrastructure as Code for all AWS resources

## Planned AWS Resources

1. **Amazon Cognito**
   - User Pool for authentication
   - Identity Pool for AWS access
   - App Client for React integration

2. **API Gateway**
   - REST API with `/chat` endpoint
   - Cognito authorizer for authentication
   - CORS configuration for React app

3. **AWS Lambda**
   - Proxy function to call AgentCore
   - Environment variables for AgentCore ARN
   - IAM role with AgentCore permissions

4. **IAM Roles and Policies**
   - Lambda execution role
   - Cognito authenticated user role
   - Permissions for AgentCore access

## Architecture Flow

```
React App → Cognito Auth → API Gateway → Lambda → AgentCore
```

1. User authenticates with Cognito
2. React app gets JWT token
3. API Gateway validates token
4. Lambda function calls AgentCore with boto3
5. Response flows back to React app

## Deployment

Will use AWS SAM or CloudFormation for infrastructure deployment:

```bash
# Deploy infrastructure
sam build
sam deploy --guided

# Update configuration
aws configure
```

## Security

- All AWS credentials stay server-side
- Cognito handles user authentication
- API Gateway validates requests
- Lambda has minimal required permissions

## Coming Soon

This infrastructure will be implemented to connect the frontend and backend components.