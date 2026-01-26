#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Creating admin user for Telemetry Dashboard${NC}"
echo "================================================"

# Get User Pool ID from CDK output
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name TelemetryDashboardStack \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
  --output text 2>/dev/null)

if [ -z "$USER_POOL_ID" ]; then
  echo -e "${RED}Error: Could not find User Pool ID.${NC}"
  echo "Make sure the CDK stack is deployed first:"
  echo "  npm run deploy"
  exit 1
fi

# User credentials
USERNAME="admin"
PASSWORD="Admin123!"
EMAIL="admin@telemetry.local"

echo -e "${YELLOW}User Pool ID:${NC} $USER_POOL_ID"
echo -e "${YELLOW}Creating user:${NC} $USERNAME"

# Check if user already exists
EXISTING_USER=$(aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username $USERNAME 2>/dev/null)

if [ $? -eq 0 ]; then
  echo -e "${YELLOW}User already exists. Resetting password...${NC}"
  
  # Reset password for existing user
  aws cognito-idp admin-set-user-password \
    --user-pool-id $USER_POOL_ID \
    --username $USERNAME \
    --password $PASSWORD \
    --permanent
    
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Password reset successfully${NC}"
  else
    echo -e "${RED}Error resetting password${NC}"
    exit 1
  fi
else
  # Create new user
  echo "Creating new user..."
  
  aws cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username $USERNAME \
    --user-attributes Name=email,Value=$EMAIL \
    --message-action SUPPRESS \
    --temporary-password "TempPass123!"
    
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error creating user${NC}"
    exit 1
  fi
  
  # Set permanent password
  aws cognito-idp admin-set-user-password \
    --user-pool-id $USER_POOL_ID \
    --username $USERNAME \
    --password $PASSWORD \
    --permanent
    
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ User created successfully${NC}"
  else
    echo -e "${RED}Error setting password${NC}"
    exit 1
  fi
fi

# Get other stack outputs
WEBSOCKET_URL=$(aws cloudformation describe-stacks \
  --stack-name TelemetryDashboardStack \
  --query "Stacks[0].Outputs[?OutputKey=='WebSocketUrl'].OutputValue" \
  --output text 2>/dev/null)

FRONTEND_URL=$(aws cloudformation describe-stacks \
  --stack-name TelemetryDashboardStack \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
  --output text 2>/dev/null)

echo ""
echo "================================================"
echo -e "${GREEN}Admin user ready!${NC}"
echo ""
echo -e "${YELLOW}Login Credentials:${NC}"
echo "  Username: $USERNAME"
echo "  Password: $PASSWORD"
echo ""
echo -e "${YELLOW}Dashboard URL:${NC}"
echo "  $FRONTEND_URL"
echo ""
echo -e "${YELLOW}WebSocket URL:${NC}"
echo "  $WEBSOCKET_URL"
echo "================================================"