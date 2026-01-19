# Video Telemetry Analytics Dashboard Architecture

## Executive Summary

A split-screen web application providing real-time video streaming telemetry visualization alongside an AI-powered chatbot for natural language data queries. The system combines live Kafka event streaming with near real-time Athena analytics.

## System Overview

### Application Layout
```
┌─────────────────────────────────────────────────────────────┐
│                         Header Bar                          │
├─────────────────────────────┬───────────────────────────────┤
│                             │                               │
│   Real-Time Dashboard       │    AI Chatbot Interface       │
│                             │                               │
│  • Live Metrics Cards       │  • Natural Language Input    │
│  • Event Stream Feed        │  • MCP Server Integration    │
│  • Quality Charts           │  • Athena Query Results      │
│  • Device Distribution      │  • Interactive Tables/Charts │
│  • Geographic Heatmap       │  • Export Capabilities       │
│                             │                               │
└─────────────────────────────┴───────────────────────────────┘
```

## Architecture Components

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  ┌────────────────────┐    ┌────────────────────┐         │
│  │  Dashboard Panel   │    │   Chatbot Panel    │         │
│  └────────────────────┘    └────────────────────┘         │
└─────────────┬──────────────────────┬───────────────────────┘
              │                      │
              │ WebSocket            │ REST API
              │                      │
┌─────────────▼──────────┐  ┌───────▼───────────┐
│  Real-Time Service     │  │   Chat API        │
│  (Node.js)            │  │   (Node.js)       │
├───────────────────────┤  ├──────────────────┤
│ • Kafka Consumer      │  │ • MCP Client     │
│ • Event Aggregation   │  │ • Session Mgmt   │
│ • WebSocket Server    │  │ • Result Format  │
└──────────┬────────────┘  └────────┬─────────┘
           │                         │
           │                         │
┌──────────▼────────────┐  ┌────────▼─────────┐
│   Amazon MSK          │  │   MCP Server     │
│   (Kafka)             │  │                  │
└───────────────────────┘  └────────┬─────────┘
                                     │
                           ┌─────────▼─────────┐
                           │   Amazon Athena   │
                           │   (S3 Data Lake)  │
                           └───────────────────┘
```

## Backend Services

### 1. Real-Time Service (Port 3001)

**Purpose**: Consume Kafka events and stream to dashboard

**Technologies**:
- Node.js with Express
- Socket.io for WebSocket connections
- kafkajs for MSK integration
- Redis for caching (optional)

**Key Features**:
- MSK IAM authentication
- Event aggregation (5-min, 1-hour windows)
- Real-time metric calculations
- Connection management

**WebSocket Events**:
```javascript
// Server → Client
'telemetry:event'     // New streaming event
'metrics:update'      // Aggregated metrics update
'viewers:count'       // Current viewer count
'quality:distribution' // Quality level breakdown
'device:distribution' // Device type breakdown
'geo:update'         // Geographic data update

// Client → Server
'subscribe:events'    // Start receiving events
'unsubscribe:events' // Stop receiving events
'filter:update'      // Update event filters
```

### 2. Chat API Service (Port 3002)

**Purpose**: Interface between frontend chat and MCP server

**Technologies**:
- Node.js with Express
- MCP client library
- Session management

**REST Endpoints**:
```
POST /api/chat/query
  Body: { message: string, sessionId: string }
  Response: { result: object, queryTime: number }

GET /api/chat/suggestions
  Response: { suggestions: string[] }

POST /api/chat/export
  Body: { data: object, format: 'csv'|'json' }
  Response: File download

GET /api/chat/history/:sessionId
  Response: { messages: array }
```

## Frontend Application

### Technology Stack
- React 18
- Material-UI or Ant Design
- Chart.js or Recharts for visualizations
- Socket.io-client for WebSocket
- React-split-pane for layout
- Axios for REST calls

### Component Structure

#### Dashboard Components
1. **MetricsCards**
   - Active Viewers
   - Events/Second
   - Error Rate
   - Average Bandwidth

2. **EventFeed**
   - Real-time scrolling list
   - Event type filters
   - Search capability
   - Color-coded by type

3. **QualityChart**
   - Pie/Donut chart
   - SD/HD/4K distribution
   - Real-time updates

4. **DeviceChart**
   - Bar chart
   - Mobile/Web/TV/Tablet
   - Click for details

5. **GeoMap**
   - Heat map visualization
   - Country/State/City levels
   - Viewer density

#### Chatbot Components
1. **ChatInterface**
   - Message input field
   - Send button
   - Voice input (optional)

2. **MessageList**
   - User/AI message bubbles
   - Timestamp display
   - Loading indicators

3. **QueryResults**
   - Table view for data
   - Chart visualizations
   - Export buttons

4. **SuggestedQueries**
   - Common query templates
   - Context-aware suggestions

## Data Flow

### Real-Time Pipeline
```
MSK Topic → Kafka Consumer → Event Processor → WebSocket → Dashboard
    ↓
  Events
    ↓
Aggregation → Metrics Cache → Periodic Updates → Charts
```

### Query Pipeline
```
User Input → Chat API → MCP Server → Athena → S3 Data
    ↓           ↓           ↓          ↓
  Query    Validation   SQL Gen    Results
    ↓           ↓           ↓          ↓
Response ← Formatting ← Processing ← Data
```

## Example Telemetry Event
```json
{
  "event_id": "EVENT_a1b2c3d4",
  "customer_id": "CUST_5e6f7g8h",
  "title_id": "TITLE_9i0j1k2l",
  "session_id": "SESSION_3m4n5o6p",
  "event_type": "start",
  "event_timestamp": "2025-08-11T14:30:45.123Z",
  "watch_duration_seconds": 1800,
  "position_seconds": 900,
  "completion_percentage": 45.5,
  "device_type": "mobile",
  "device_os": "iOS",
  "quality": "HD",
  "bandwidth_mbps": 25.5,
  "buffering_events": 2,
  "country": "United States",
  "state": "California",
  "city": "Los Angeles"
}
```

## Example MCP Queries

### Basic Queries
- "How many viewers are currently watching?"
- "What's the average buffering rate?"
- "Show me the top 10 titles today"

### Advanced Queries
- "Compare HD vs 4K completion rates for mobile devices"
- "What's the correlation between bandwidth and buffering events?"
- "Show viewer distribution by time zone for prime time hours"

### Analytical Queries
- "Calculate the 95th percentile of buffering duration by ISP"
- "What's the viewer retention rate for content longer than 1 hour?"
- "Show me anomalies in error rates over the last 24 hours"

## Performance Considerations

### Scalability
- WebSocket connection pooling (max 1000 concurrent)
- Event batching (100 events per batch)
- Metric aggregation intervals (5 sec minimum)
- Query result caching (5 min TTL)

### Optimization
- Lazy loading for chart components
- Virtual scrolling for event feed
- Debounced filter updates
- Progressive data loading

### Monitoring
- CloudWatch metrics integration
- Error tracking with Sentry
- Performance monitoring
- Connection health checks

## Security

### Authentication
- JWT tokens for API access
- Session management
- CORS configuration
- Rate limiting

### Data Protection
- PII masking in logs
- Encrypted WebSocket connections
- Secure MCP communication
- API key management

## Deployment

### Docker Configuration
```yaml
services:
  realtime-service:
    build: ./backend/realtime-service
    ports: ["3001:3001"]
    environment:
      - MSK_BOOTSTRAP_SERVERS
      - AWS_REGION
    
  chat-api:
    build: ./backend/chat-api
    ports: ["3002:3002"]
    environment:
      - MCP_SERVER_URL
      - MCP_API_KEY
    
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - REACT_APP_WS_URL
      - REACT_APP_CHAT_API_URL
```

### AWS Infrastructure
- ECS Fargate for container hosting
- Application Load Balancer
- CloudFront for frontend CDN
- Route53 for DNS
- VPC with private subnets for services

## Development Phases

### Phase 1: Foundation (Week 1-2)
- Setup project structure
- Basic Kafka consumer
- Simple WebSocket server
- Basic React layout

### Phase 2: Real-Time Dashboard (Week 3-4)
- Implement all dashboard components
- Event aggregation logic
- Real-time charts
- WebSocket optimization

### Phase 3: Chat Integration (Week 5-6)
- MCP client setup
- Chat UI implementation
- Query result formatting
- Session management

### Phase 4: Polish & Deploy (Week 7-8)
- Error handling
- Performance optimization
- Docker configuration
- AWS deployment

## Success Metrics
- Dashboard latency < 100ms
- Query response time < 2 seconds
- 99.9% uptime
- Support 1000+ concurrent users
- WebSocket reconnection reliability

## Future Enhancements
- Machine learning for anomaly detection
- Predictive analytics
- Mobile responsive design
- Alert system for thresholds
- Historical data comparison
- Multi-tenant support
- Custom dashboard layouts
- Scheduled reports