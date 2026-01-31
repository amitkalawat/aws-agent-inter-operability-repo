# ACME Corp Chat - React Frontend

A modern React frontend for the ACME Corp AgentCore chatbot with Amazon Cognito authentication.

## 🌟 Features

- **🔐 Cognito Authentication**: Secure login with Amazon Cognito User Pool
- **🤖 AgentCore Integration**: Direct communication with Amazon Bedrock AgentCore
- **💬 Real-time Chat**: Modern chat interface with streaming responses
- **🎨 Modern UI**: Clean design with responsive layout
- **📱 Responsive**: Works on desktop and mobile devices
- **⚡ Fast**: Built with React and TypeScript for optimal performance

## 🚀 Quick Start

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Running AgentCore deployment with JWT authentication

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend/acme-chat
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and go to: http://localhost:3000

## 🔧 Configuration

Configuration is managed via environment variables generated from CloudFormation outputs:

```bash
# Generate .env from deployed stack
cd acme-chat
./scripts/deploy-frontend.sh
```

The `.env` file contains:
```
REACT_APP_COGNITO_USER_POOL_ID=us-west-2_XXXXXXXXX
REACT_APP_COGNITO_APP_CLIENT_ID=XXXXXXXXXXXXXXXXXX
REACT_APP_AGENTCORE_ARN=arn:aws:bedrock-agentcore:us-west-2:ACCOUNT:runtime/NAME
```

## 👤 Test Account

Create a test user after deployment (see agent-stack/cdk/README.md for instructions):
- **Username**: user1@test.com
- **Password**: Abcd1234@

## 🛠 How It Works

### Authentication Flow

1. **Login**: User enters credentials or uses demo account
2. **Cognito Auth**: amazon-cognito-identity-js authenticates with Cognito
3. **Token Retrieval**: Access token is obtained for API calls
4. **Session Management**: Token is stored for subsequent requests

### Chat Integration

1. **Connection Test**: App tests connection to AgentCore on load
2. **Message Sending**: User messages are sent via HTTP POST with bearer token
3. **Response Handling**: AgentCore responses are displayed in chat interface
4. **Session Management**: Maintains conversation context

### API Communication

The app uses direct HTTP requests to communicate with AgentCore:

```typescript
// Headers required for authenticated requests
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json',
  'X-Amzn-Trace-Id': traceId,
  'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,
};

// POST to AgentCore endpoint
const response = await axios.post(
  `https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/${encodedArn}/invocations?qualifier=DEFAULT`,
  { prompt: userMessage },
  { headers }
);
```

## 📁 Project Structure

```
frontend/acme-chat/
├── src/
│   ├── components/           # React components
│   │   ├── Header.tsx       # App header with user info
│   │   ├── LoginForm.tsx    # Authentication form
│   │   └── ChatInterface.tsx# Main chat interface
│   ├── services/            # Business logic
│   │   ├── AuthService.ts   # Cognito authentication
│   │   └── AgentCoreService.ts # AgentCore communication
│   ├── config.ts           # App configuration
│   ├── App.tsx             # Main app component
│   └── App.css             # Styles
├── public/                 # Static assets
└── package.json           # Dependencies and scripts
```

## 🎨 UI Components

### Login Form
- Username/password input fields
- Show/hide password toggle
- Demo account button
- Loading states and error handling

### Chat Interface
- **Connection Status**: Shows AgentCore connectivity
- **Message History**: Scrollable chat history
- **Typing Indicators**: Shows when AI is responding
- **New Chat Button**: Resets conversation
- **Message Input**: Multi-line input with send button

### Header
- App title and subtitle
- User authentication status
- Sign out functionality

## 🔒 Security Features

- **JWT Authentication**: All API calls use bearer tokens
- **Token Management**: Automatic token refresh and validation
- **Session Handling**: Secure session management
- **Input Sanitization**: Safe handling of user input
- **CORS Compliance**: Proper cross-origin request handling

## 🧪 Testing Features

The app includes comprehensive testing capabilities:

1. **Connection Testing**: Automatic AgentCore connectivity check
2. **Authentication Testing**: Login/logout flow validation
3. **Message Testing**: Various prompt types (math, general knowledge, conversation)
4. **Error Handling**: Graceful handling of network and authentication errors

## 📱 Responsive Design

- **Mobile-First**: Optimized for mobile devices
- **Flexible Layout**: Adapts to different screen sizes
- **Touch-Friendly**: Large buttons and touch targets
- **Readable Typography**: Optimized font sizes and spacing

## 🚀 Deployment

For production deployment:

1. Build the app:
   ```bash
   npm run build
   ```

2. Deploy the `build/` directory to your web server
3. Configure HTTPS for secure token transmission
4. Update CORS settings in AgentCore if needed

## 🔧 Troubleshooting

### Common Issues

1. **"Connection Error"**: Check AgentCore deployment and region settings
2. **"Authentication Failed"**: Verify Cognito configuration and credentials
3. **"Network Error"**: Check internet connectivity and CORS settings
4. **Token Errors**: Ensure token hasn't expired (24-hour validity)

### Debug Steps

1. Open browser developer tools (F12)
2. Check Network tab for failed requests
3. Check Console tab for JavaScript errors
4. Verify configuration in `src/config.ts`

## 📚 Dependencies

Key dependencies:
- **React**: UI framework
- **TypeScript**: Type safety
- **amazon-cognito-identity-js**: Cognito authentication
- **axios**: HTTP client for API calls

## 🎯 Features Demonstrated

This frontend demonstrates:
- ✅ Cognito User Pool authentication
- ✅ JWT bearer token handling
- ✅ Direct AgentCore HTTP API calls
- ✅ Real-time chat interface
- ✅ Session management
- ✅ Error handling and retry logic
- ✅ Responsive modern UI design
- ✅ TypeScript implementation

## 🔗 Related

- [Backend AgentCore Deployment](../backend/README.md)
- [Infrastructure Setup](../infrastructure/README.md)
- [Authentication Testing](../backend/deployment/test_http_auth.py)

---

**Built with ❤️ for ACME Corp - Powered by Amazon Bedrock AgentCore**