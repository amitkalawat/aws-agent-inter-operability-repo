# Telemetry Dashboard CDK Stack

A serverless real-time video telemetry dashboard built with AWS CDK, featuring MSK integration, WebSocket streaming, and Cognito authentication.

## Architecture

- **Frontend**: React app hosted on S3/CloudFront
- **Authentication**: AWS Cognito with admin user
- **Real-time API**: API Gateway WebSocket
- **Event Processing**: Lambda functions consuming from MSK
- **Storage**: DynamoDB for connection management
- **Streaming**: MSK (Kafka) with IAM authentication

## Prerequisites

- Node.js 18+ and npm
- AWS CLI configured with credentials
- AWS CDK CLI: `npm install -g aws-cdk`
- An existing MSK cluster with IAM authentication enabled
- VPC with private subnets for Lambda functions

## Project Structure

```
telemetry-dashboard-cdk/
├── bin/                    # CDK app entry point
├── lib/                    # CDK stack definitions
│   ├── constructs/        # Reusable CDK constructs
│   └── telemetry-dashboard-stack.ts
├── backend/               # Lambda functions
│   └── lambdas/
│       ├── websocket/     # WebSocket handlers
│       ├── msk/          # MSK consumer
│       └── authorizer/   # Cognito authorizer
├── frontend/             # React application
└── scripts/              # Utility scripts
```

## Deployment

### 1. Install Dependencies

```bash
cd telemetry-dashboard-cdk
npm install

# Install Lambda dependencies
cd backend/lambdas/websocket && npm install && cd ../../..
cd backend/lambdas/msk && npm install && cd ../../..
cd backend/lambdas/authorizer && npm install && cd ../../..
```

### 2. Configure Environment

Set the required environment variables:

```bash
export MSK_CLUSTER_ARN="arn:aws:kafka:region:account:cluster/name/id"
export MSK_SECURITY_GROUP_ID="sg-xxxxx"
export VPC_ID="vpc-xxxxx"
export PRIVATE_SUBNET_IDS="subnet-xxx,subnet-yyy"
```

Or create a `.env` file:

```env
MSK_CLUSTER_ARN=arn:aws:kafka:region:account:cluster/name/id
MSK_SECURITY_GROUP_ID=sg-xxxxx
VPC_ID=vpc-xxxxx
PRIVATE_SUBNET_IDS=subnet-xxx,subnet-yyy
```

### 3. Bootstrap CDK (first time only)

```bash
cdk bootstrap
```

### 4. Deploy the Stack

```bash
npm run deploy
```

This will:
- Create Cognito User Pool
- Deploy WebSocket API with Lambda handlers
- Set up MSK consumer with event source mapping
- Create DynamoDB table for connections
- Deploy frontend to S3/CloudFront
- Output all necessary URLs and IDs

### 5. Create Admin User

After deployment, create the admin user:

```bash
npm run create-admin
```

This creates a user with:
- Username: `admin`
- Password: `Admin123!`

## Stack Outputs

After deployment, you'll see:

- **UserPoolId**: Cognito User Pool ID
- **UserPoolClientId**: Cognito app client ID
- **WebSocketUrl**: WebSocket API endpoint
- **FrontendUrl**: CloudFront URL for the dashboard
- **Region**: AWS region

## Testing the Dashboard

1. Open the **FrontendUrl** in your browser
2. Login with `admin` / `Admin123!`
3. Click "Connect" to start receiving telemetry events
4. Events from MSK will stream in real-time

## Lambda Functions

### WebSocket Handlers

- **connect.js**: Stores connection in DynamoDB
- **disconnect.js**: Removes connection from DynamoDB
- **default.js**: Handles WebSocket messages (ping/pong, subscribe)

### MSK Consumer

- **consumer.js**: Processes Kafka events and broadcasts to WebSocket clients
- Triggered by Lambda Event Source Mapping
- Uses IAM authentication with MSK

### Authorizer

- **wsAuthorizer.js**: Validates Cognito JWT tokens for WebSocket connections

## Configuration Options

### CDK Context Variables

You can also pass configuration via CDK context:

```bash
cdk deploy \
  -c mskClusterArn=arn:aws:kafka:... \
  -c mskSecurityGroupId=sg-xxx \
  -c vpcId=vpc-xxx \
  -c privateSubnetIds=subnet-xxx,subnet-yyy
```

### Customizing the Stack

Edit `lib/telemetry-dashboard-stack.ts` to modify:
- DynamoDB table settings
- Lambda function configurations
- API Gateway settings
- CloudFront distribution settings

## Monitoring

### CloudWatch Logs

Log groups are created for each Lambda function:
- `/aws/lambda/TelemetryDashboardStack-WebSocketApiConnectHandler*`
- `/aws/lambda/TelemetryDashboardStack-WebSocketApiDisconnectHandler*`
- `/aws/lambda/TelemetryDashboardStack-MskConsumerConsumerFunction*`

### Metrics

Monitor in CloudWatch:
- Lambda invocations and errors
- API Gateway connections
- DynamoDB read/write capacity
- MSK consumer lag

## Cleanup

To remove all resources:

```bash
npm run destroy
```

Or:

```bash
cdk destroy
```

## Troubleshooting

### MSK Connection Issues

1. Verify Lambda functions are in the same VPC as MSK
2. Check security group allows traffic on port 9098 (IAM auth)
3. Ensure Lambda execution role has MSK permissions

### WebSocket Connection Issues

1. Check Cognito token is valid
2. Verify API Gateway endpoint URL
3. Check Lambda function logs for errors

### Frontend Not Loading

1. Ensure frontend is built: `cd frontend && npm run build`
2. Redeploy after building: `npm run deploy`
3. Check CloudFront distribution status

## Development

### Local Testing

For Lambda functions:
```bash
cd backend/lambdas/websocket
node -e "require('./connect').handler({...})"
```

### Adding New Features

1. Modify CDK constructs in `lib/constructs/`
2. Update Lambda handlers in `backend/lambdas/`
3. Run `npm run synth` to check CloudFormation template
4. Deploy with `npm run deploy`

## Security Considerations

- Cognito tokens expire after 1 hour
- WebSocket connections have 2-hour maximum duration
- DynamoDB items have TTL set to 2 hours
- All data in transit is encrypted (HTTPS/WSS)
- MSK uses IAM authentication
- CloudFront uses Origin Access Identity for S3

## Cost Optimization

- DynamoDB uses on-demand billing
- Lambda functions are pay-per-invocation
- CloudFront is in PriceClass_100 (US, Canada, Europe)
- Consider setting up CloudWatch alarms for cost monitoring

## Support

For issues:
1. Check CloudWatch Logs for Lambda errors
2. Verify all environment variables are set
3. Ensure MSK cluster is running and accessible
4. Check IAM permissions for all services

## License

This project is part of the ACME Video Telemetry Platform.