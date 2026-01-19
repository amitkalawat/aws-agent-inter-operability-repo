# Project Structure

Detailed file structure and component descriptions for the Video Telemetry Analytics Dashboard.

## Complete File Tree

```
producer_dashboard/
│
├── backend/
│   ├── realtime-service/
│   │   ├── src/
│   │   │   ├── config/
│   │   │   │   ├── kafka.config.js      # MSK configuration
│   │   │   │   ├── redis.config.js      # Redis cache config
│   │   │   │   └── aws.config.js        # AWS SDK setup
│   │   │   │
│   │   │   ├── consumers/
│   │   │   │   ├── kafka-consumer.js    # Main Kafka consumer
│   │   │   │   └── event-handler.js     # Event processing logic
│   │   │   │
│   │   │   ├── processors/
│   │   │   │   ├── aggregator.js        # Metric aggregation
│   │   │   │   ├── geo-processor.js     # Geographic data
│   │   │   │   └── quality-analyzer.js  # Quality metrics
│   │   │   │
│   │   │   ├── websocket/
│   │   │   │   ├── socket-server.js     # Socket.io server
│   │   │   │   ├── event-emitter.js     # Event broadcasting
│   │   │   │   └── connection-mgr.js    # Connection management
│   │   │   │
│   │   │   ├── utils/
│   │   │   │   ├── logger.js            # Winston logger
│   │   │   │   ├── metrics.js           # CloudWatch metrics
│   │   │   │   └── cache.js             # Cache utilities
│   │   │   │
│   │   │   └── index.js                 # Main entry point
│   │   │
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   │
│   │   ├── .env.example
│   │   ├── .eslintrc.js
│   │   ├── jest.config.js
│   │   ├── package.json
│   │   └── Dockerfile
│   │
│   └── chat-api/
│       ├── src/
│       │   ├── config/
│       │   │   ├── mcp.config.js        # MCP server config
│       │   │   └── app.config.js        # Express config
│       │   │
│       │   ├── controllers/
│       │   │   ├── chat.controller.js   # Chat endpoints
│       │   │   ├── export.controller.js # Export functionality
│       │   │   └── health.controller.js # Health checks
│       │   │
│       │   ├── services/
│       │   │   ├── mcp-client.js        # MCP integration
│       │   │   ├── query-processor.js   # Query handling
│       │   │   ├── result-formatter.js  # Result formatting
│       │   │   └── session-manager.js   # Session handling
│       │   │
│       │   ├── middleware/
│       │   │   ├── auth.js              # Authentication
│       │   │   ├── rate-limiter.js      # Rate limiting
│       │   │   └── error-handler.js     # Error handling
│       │   │
│       │   ├── routes/
│       │   │   ├── chat.routes.js       # Chat routes
│       │   │   └── index.js             # Route aggregator
│       │   │
│       │   ├── utils/
│       │   │   ├── logger.js            # Logging utility
│       │   │   └── validators.js        # Input validation
│       │   │
│       │   └── server.js                # Express server
│       │
│       ├── tests/
│       ├── .env.example
│       ├── package.json
│       └── Dockerfile
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   ├── favicon.ico
│   │   └── manifest.json
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   │   ├── MetricsCards/
│   │   │   │   │   ├── MetricsCards.jsx
│   │   │   │   │   ├── MetricCard.jsx
│   │   │   │   │   └── MetricsCards.css
│   │   │   │   │
│   │   │   │   ├── EventFeed/
│   │   │   │   │   ├── EventFeed.jsx
│   │   │   │   │   ├── EventItem.jsx
│   │   │   │   │   ├── EventFilter.jsx
│   │   │   │   │   └── EventFeed.css
│   │   │   │   │
│   │   │   │   ├── Charts/
│   │   │   │   │   ├── QualityChart.jsx
│   │   │   │   │   ├── DeviceChart.jsx
│   │   │   │   │   ├── TimeSeriesChart.jsx
│   │   │   │   │   └── ChartUtils.js
│   │   │   │   │
│   │   │   │   ├── GeoMap/
│   │   │   │   │   ├── GeoMap.jsx
│   │   │   │   │   ├── MapControls.jsx
│   │   │   │   │   └── GeoMap.css
│   │   │   │   │
│   │   │   │   └── index.js
│   │   │   │
│   │   │   ├── Chatbot/
│   │   │   │   ├── ChatContainer/
│   │   │   │   │   ├── ChatContainer.jsx
│   │   │   │   │   └── ChatContainer.css
│   │   │   │   │
│   │   │   │   ├── MessageList/
│   │   │   │   │   ├── MessageList.jsx
│   │   │   │   │   ├── Message.jsx
│   │   │   │   │   └── MessageList.css
│   │   │   │   │
│   │   │   │   ├── MessageInput/
│   │   │   │   │   ├── MessageInput.jsx
│   │   │   │   │   └── MessageInput.css
│   │   │   │   │
│   │   │   │   ├── QueryResults/
│   │   │   │   │   ├── QueryResults.jsx
│   │   │   │   │   ├── ResultTable.jsx
│   │   │   │   │   ├── ResultChart.jsx
│   │   │   │   │   └── ExportButton.jsx
│   │   │   │   │
│   │   │   │   ├── SuggestedQueries/
│   │   │   │   │   ├── SuggestedQueries.jsx
│   │   │   │   │   └── queries.json
│   │   │   │   │
│   │   │   │   └── index.js
│   │   │   │
│   │   │   └── Layout/
│   │   │       ├── SplitView/
│   │   │       │   ├── SplitView.jsx
│   │   │       │   └── SplitView.css
│   │   │       │
│   │   │       ├── Header/
│   │   │       │   ├── Header.jsx
│   │   │       │   └── Header.css
│   │   │       │
│   │   │       └── ErrorBoundary/
│   │   │           └── ErrorBoundary.jsx
│   │   │
│   │   ├── services/
│   │   │   ├── websocket.service.js     # Socket.io client
│   │   │   ├── chat.service.js          # Chat API calls
│   │   │   ├── export.service.js        # Export functionality
│   │   │   └── storage.service.js       # Local storage
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js          # WebSocket hook
│   │   │   ├── useChat.js               # Chat functionality
│   │   │   ├── useMetrics.js            # Metrics updates
│   │   │   └── useFilters.js            # Filter management
│   │   │
│   │   ├── utils/
│   │   │   ├── constants.js             # App constants
│   │   │   ├── formatters.js            # Data formatters
│   │   │   ├── validators.js            # Input validators
│   │   │   └── helpers.js               # Helper functions
│   │   │
│   │   ├── styles/
│   │   │   ├── index.css                # Global styles
│   │   │   ├── variables.css            # CSS variables
│   │   │   └── themes/
│   │   │       ├── light.css
│   │   │       └── dark.css
│   │   │
│   │   ├── App.jsx                      # Main app component
│   │   ├── App.css
│   │   ├── index.js                     # React entry point
│   │   └── setupTests.js
│   │
│   ├── .env.example
│   ├── .eslintrc.js
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf                       # Production nginx config
│
├── docker/
│   ├── docker-compose.yml               # Full stack compose
│   ├── docker-compose.dev.yml           # Development compose
│   └── docker-compose.prod.yml          # Production compose
│
├── scripts/
│   ├── setup.sh                         # Initial setup script
│   ├── start-dev.sh                     # Start dev environment
│   ├── build.sh                         # Build all services
│   └── deploy.sh                        # Deploy to AWS
│
├── docs/
│   ├── API.md                           # API documentation
│   ├── DEPLOYMENT.md                    # Deployment guide
│   ├── TROUBLESHOOTING.md              # Common issues
│   └── CONTRIBUTING.md                  # Contribution guide
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                      # CI pipeline
│   │   └── deploy.yml                  # CD pipeline
│   └── ISSUE_TEMPLATE/
│
├── .env.example                         # Root environment template
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── PROJECT_STRUCTURE.md
└── LICENSE
```

## Component Descriptions

### Backend Services

#### Real-Time Service Components

**Kafka Consumer (`kafka-consumer.js`)**
- Connects to MSK cluster with IAM auth
- Consumes from `acme-telemetry` topic
- Handles reconnection and error recovery
- Batch processing for efficiency

**Event Aggregator (`aggregator.js`)**
- 5-minute window aggregations
- Hourly rollups
- Real-time metric calculations
- Cache management

**WebSocket Server (`socket-server.js`)**
- Socket.io implementation
- Room-based broadcasting
- Connection pooling
- Heartbeat monitoring

#### Chat API Components

**MCP Client (`mcp-client.js`)**
- MCP server connection
- Query submission
- Response handling
- Error recovery

**Query Processor (`query-processor.js`)**
- Query validation
- Context enhancement
- Result caching
- Query history

**Session Manager (`session-manager.js`)**
- User session tracking
- Query history per session
- Session cleanup
- State management

### Frontend Components

#### Dashboard Components

**MetricsCards**
```jsx
// Key metrics display
- Active Viewers (real-time count)
- Events/Second (rate calculation)
- Error Rate (percentage)
- Avg Bandwidth (Mbps)
```

**EventFeed**
```jsx
// Live event stream
- Virtual scrolling for performance
- Type-based color coding
- Search and filter controls
- Event details on hover
```

**QualityChart**
```jsx
// Quality distribution visualization
- Pie/Donut chart
- SD/HD/4K breakdown
- Click for detailed view
- Real-time updates
```

**DeviceChart**
```jsx
// Device type distribution
- Bar/Column chart
- Mobile/Web/TV/Tablet
- Percentage labels
- Drill-down capability
```

**GeoMap**
```jsx
// Geographic visualization
- Heat map overlay
- Country/State/City levels
- Zoom controls
- Density indicators
```

#### Chatbot Components

**ChatContainer**
```jsx
// Main chat wrapper
- Message state management
- API integration
- Error handling
- Loading states
```

**MessageList**
```jsx
// Conversation display
- User/AI message bubbles
- Timestamp formatting
- Auto-scroll to bottom
- Message animations
```

**MessageInput**
```jsx
// User input interface
- Text input field
- Send button
- Enter key handling
- Character limit
```

**QueryResults**
```jsx
// Result visualization
- Table view for data
- Chart options
- Export functionality
- Pagination
```

**SuggestedQueries**
```jsx
// Query templates
- Common queries list
- Context-aware suggestions
- One-click execution
- Category grouping
```

### Service Layer

#### WebSocket Service
```javascript
// Real-time connection management
class WebSocketService {
  - connect()
  - disconnect()
  - subscribe(event, callback)
  - emit(event, data)
  - reconnect()
}
```

#### Chat Service
```javascript
// Chat API interactions
class ChatService {
  - sendQuery(message, sessionId)
  - getSuggestions()
  - getHistory(sessionId)
  - exportData(data, format)
}
```

### Custom Hooks

**useWebSocket**
```javascript
// WebSocket connection hook
const { connected, data, error } = useWebSocket(url);
```

**useChat**
```javascript
// Chat functionality hook
const { messages, sendMessage, loading } = useChat();
```

**useMetrics**
```javascript
// Metrics subscription hook
const { metrics, lastUpdate } = useMetrics();
```

**useFilters**
```javascript
// Filter management hook
const { filters, setFilter, clearFilters } = useFilters();
```

## Configuration Files

### Backend Configuration

**kafka.config.js**
```javascript
module.exports = {
  brokers: process.env.MSK_BOOTSTRAP_SERVERS.split(','),
  topic: process.env.MSK_TOPIC,
  groupId: 'dashboard-consumer',
  sasl: {
    mechanism: 'aws-iam',
    authorizationIdentity: process.env.AWS_IAM_ROLE
  }
};
```

**mcp.config.js**
```javascript
module.exports = {
  serverUrl: process.env.MCP_SERVER_URL,
  apiKey: process.env.MCP_API_KEY,
  timeout: 30000,
  retries: 3
};
```

### Frontend Configuration

**constants.js**
```javascript
export const WS_EVENTS = {
  TELEMETRY_EVENT: 'telemetry:event',
  METRICS_UPDATE: 'metrics:update',
  VIEWERS_COUNT: 'viewers:count'
};

export const CHART_COLORS = {
  SD: '#FFA726',
  HD: '#66BB6A',
  '4K': '#42A5F5'
};
```

## Docker Configuration

### docker-compose.yml
```yaml
version: '3.8'

services:
  realtime-service:
    build: ./backend/realtime-service
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
    networks:
      - app-network

  chat-api:
    build: ./backend/chat-api
    ports:
      - "3002:3002"
    environment:
      - NODE_ENV=production
    networks:
      - app-network

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - realtime-service
      - chat-api
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

## Scripts

### setup.sh
```bash
#!/bin/bash
# Initial project setup
npm install --prefix backend/realtime-service
npm install --prefix backend/chat-api
npm install --prefix frontend
cp .env.example .env
echo "Setup complete! Edit .env file with your configuration."
```

### start-dev.sh
```bash
#!/bin/bash
# Start development environment
docker-compose -f docker/docker-compose.dev.yml up
```

## Testing Structure

### Unit Tests
- Component testing with Jest
- Service mocking
- Snapshot testing
- Coverage reports

### Integration Tests
- API endpoint testing
- WebSocket connection tests
- MCP integration tests
- End-to-end flows

## Build and Deployment

### Build Process
1. Lint and test all services
2. Build Docker images
3. Push to ECR
4. Update ECS task definitions
5. Deploy to ECS cluster

### CI/CD Pipeline
- GitHub Actions workflow
- Automated testing
- Docker image building
- AWS deployment
- Rollback capability