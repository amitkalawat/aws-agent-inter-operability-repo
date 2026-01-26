# Video Telemetry Analytics Dashboard

A real-time analytics platform combining live streaming telemetry visualization with AI-powered natural language querying capabilities.

## Overview

This application provides a comprehensive view of video streaming telemetry data through:
- **Real-time Dashboard**: Live metrics from Kafka streaming events
- **AI Chatbot**: Natural language queries via MCP server to Athena

## Features

### Real-Time Dashboard (Left Panel)
- 📊 Live streaming metrics and KPIs
- 📈 Real-time event feed with filtering
- 🗺️ Geographic distribution heatmap
- 📱 Device and quality distribution charts
- ⚡ Performance metrics (buffering, errors)

### AI Chat Interface (Right Panel)
- 💬 Natural language data queries
- 🤖 MCP server integration for Athena
- 📊 Interactive result visualizations
- 💾 Export capabilities (CSV/JSON)
- 🔍 Query suggestions and templates

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Docker and Docker Compose
- AWS credentials configured
- Access to MSK cluster
- MCP server endpoint

### Installation

1. Clone the repository:
```bash
cd producer_dashboard
```

2. Install dependencies:
```bash
# Backend services
cd backend/realtime-service && npm install
cd ../chat-api && npm install

# Frontend
cd ../../frontend && npm install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start services:
```bash
# Using Docker Compose
docker-compose up

# Or manually
npm run start:backend
npm run start:frontend
```

5. Access the application:
```
http://localhost:3000
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Kafka Configuration
MSK_BOOTSTRAP_SERVERS=your-msk-cluster.kafka.us-west-2.amazonaws.com:9092
MSK_TOPIC=acme-telemetry
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# MCP Server
MCP_SERVER_URL=https://your-mcp-server.com
MCP_API_KEY=your-mcp-api-key

# Service Ports
REALTIME_SERVICE_PORT=3001
CHAT_API_PORT=3002
FRONTEND_PORT=3000

# Frontend URLs
REACT_APP_WS_URL=http://localhost:3001
REACT_APP_CHAT_API_URL=http://localhost:3002
```

## Usage

### Dashboard Features

#### Viewing Real-Time Metrics
The dashboard automatically connects to the Kafka stream and displays:
- Current viewer count
- Events per second
- Quality distribution (SD/HD/4K)
- Device type breakdown
- Geographic distribution

#### Filtering Events
Use the filter controls to:
- Filter by event type (start, stop, pause, resume, complete)
- Filter by device type
- Filter by quality level
- Search by customer or session ID

### Chatbot Queries

#### Example Queries
Ask natural language questions like:
- "How many viewers are currently watching?"
- "What's the most popular content today?"
- "Show me buffering rates by ISP"
- "Compare mobile vs TV viewing patterns"
- "What's the average completion rate for 4K content?"

#### Query Results
Results are displayed as:
- Formatted tables
- Interactive charts
- Summary statistics
- Exportable data (CSV/JSON)

## Development

### Project Structure
```
producer_dashboard/
├── backend/
│   ├── realtime-service/    # Kafka consumer & WebSocket
│   └── chat-api/            # MCP client & chat logic
├── frontend/                # React application
├── docker-compose.yml       # Container orchestration
└── docs/                    # Documentation
```

### Running in Development

1. Start backend services:
```bash
cd backend/realtime-service
npm run dev

# In another terminal
cd backend/chat-api
npm run dev
```

2. Start frontend:
```bash
cd frontend
npm start
```

### Testing

Run tests:
```bash
# Backend tests
cd backend/realtime-service && npm test
cd backend/chat-api && npm test

# Frontend tests
cd frontend && npm test
```

## API Documentation

### WebSocket Events (Port 3001)

**Subscribe to events:**
```javascript
socket.emit('subscribe:events');
```

**Receive telemetry events:**
```javascript
socket.on('telemetry:event', (event) => {
  console.log('New event:', event);
});
```

**Receive metric updates:**
```javascript
socket.on('metrics:update', (metrics) => {
  console.log('Updated metrics:', metrics);
});
```

### REST API Endpoints (Port 3002)

**Submit chat query:**
```http
POST /api/chat/query
Content-Type: application/json

{
  "message": "How many viewers are watching HD content?",
  "sessionId": "session-123"
}
```

**Get query suggestions:**
```http
GET /api/chat/suggestions
```

**Export data:**
```http
POST /api/chat/export
Content-Type: application/json

{
  "data": {...},
  "format": "csv"
}
```

## Monitoring

### Health Checks
- Real-time service: `http://localhost:3001/health`
- Chat API: `http://localhost:3002/health`

### Metrics
The application exposes metrics for:
- WebSocket connections
- Kafka consumer lag
- Query response times
- Error rates

## Troubleshooting

### Common Issues

#### Kafka Connection Failed
- Verify MSK cluster is accessible
- Check AWS credentials
- Ensure security group allows traffic

#### MCP Server Timeout
- Verify MCP server URL
- Check API key validity
- Review network connectivity

#### WebSocket Disconnections
- Check browser console for errors
- Verify WebSocket URL configuration
- Review server logs

### Debug Mode
Enable debug logging:
```bash
DEBUG=* npm start
```

## Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

### AWS ECS Deployment
1. Build and push images to ECR
2. Create ECS task definitions
3. Configure ALB for load balancing
4. Deploy services to ECS cluster

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed instructions.

## Performance

### Optimization Tips
- Enable Redis caching for metrics
- Use CDN for static assets
- Implement query result caching
- Configure connection pooling

### Benchmarks
- Dashboard latency: < 100ms
- Query response: < 2 seconds
- Supports 1000+ concurrent users
- 99.9% uptime SLA

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues and questions:
- Check [ARCHITECTURE.md](./ARCHITECTURE.md) for technical details
- Review [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for code organization
- Open an issue on GitHub

## License

This project is part of the ACME Video Telemetry Platform.

## Acknowledgments

- Built with React, Node.js, and Socket.io
- Powered by Amazon MSK and Athena
- MCP server for natural language processing