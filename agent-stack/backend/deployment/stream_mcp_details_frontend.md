# Plan: Stream MCP Server Information to Frontend During Tool Calls

## Objective
Display real-time information about which MCP server (hosted on Bedrock AgentCore runtime) is being used when tools are invoked, providing visibility into the multi-MCP architecture.

## Current State Analysis

### 1. MCP Tools Available
- **AWS Documentation MCP** (`MCP_DOCS_URL`)
- **Data Processing MCP** (`MCP_DATAPROC_URL`)
- **Code Interpreter** (local tool, not MCP)

### 2. Tool Registration
- Tools are registered via `list_tools_sync()` from each MCP client
- Combined into `all_tools` list passed to Strands Agent
- Tool names are logged but not streamed to frontend

### 3. Streaming Architecture
- Uses `extract_text_from_event()` to parse Strands events
- Yields text chunks for streaming
- No current mechanism for tool metadata streaming

## Implementation Plan

### Phase 1: Create Tool Tracking Wrapper

**New File: `backend/agent/mcp_tool_tracker.py`**

```python
"""
MCP Tool Tracker for monitoring which MCP server handles each tool invocation
"""
from typing import Dict, List, Any

class MCPToolTracker:
    def __init__(self):
        self.tool_mapping = {}  # tool_name -> MCP server info
        
    def register_tools(self, tools: List[Any], mcp_name: str, mcp_url: str):
        """
        Map tool names to their MCP server
        
        Args:
            tools: List of tool objects from MCP client
            mcp_name: Human-readable name of the MCP server
            mcp_url: URL endpoint of the MCP server
        """
        for tool in tools:
            tool_name = getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown'))
            self.tool_mapping[tool_name] = {
                'mcp_name': mcp_name,
                'mcp_url': mcp_url,
                'server_type': 'bedrock-agentcore-runtime'
            }
    
    def get_tool_info(self, tool_name: str) -> Dict[str, str]:
        """
        Get MCP server info for a tool
        
        Args:
            tool_name: Name of the tool being invoked
            
        Returns:
            Dictionary with MCP server information
        """
        return self.tool_mapping.get(tool_name, {
            'mcp_name': 'local',
            'mcp_url': 'N/A',
            'server_type': 'local'
        })
    
    def get_all_mappings(self) -> Dict[str, Dict[str, str]]:
        """Return all tool to MCP mappings"""
        return self.tool_mapping.copy()
```

### Phase 2: Modify strands_claude.py to Track Tools

#### 2.1 Import and Initialize Tracker

```python
# Add to imports
from mcp_tool_tracker import MCPToolTracker

# Initialize globally (after model initialization)
tool_tracker = MCPToolTracker()
```

#### 2.2 Register Tools with Metadata

```python
# In create_agent_with_memory() function, after getting tools:

# When loading AWS docs tools
if aws_docs_client:
    aws_tools = aws_docs_client.list_tools_sync()
    credentials = secrets_manager.get_mcp_credentials()
    tool_tracker.register_tools(
        aws_tools, 
        'AWS Documentation MCP',
        credentials.get('MCP_DOCS_URL', 'https://aws-docs-mcp.bedrock-agentcore.amazonaws.com')
    )
    print(f"📚 Registered {len(aws_tools)} AWS Documentation tools")

# When loading dataproc tools
if dataproc_client:
    dataproc_tools = dataproc_client.list_tools_sync()
    tool_tracker.register_tools(
        dataproc_tools,
        'Data Processing MCP', 
        credentials.get('MCP_DATAPROC_URL', 'https://dataproc-mcp.bedrock-agentcore.amazonaws.com')
    )
    print(f"📊 Registered {len(dataproc_tools)} Data Processing tools")

# Register code interpreter
tool_tracker.register_tools(
    [execute_code_with_visualization],
    'Code Interpreter',
    'local://code-interpreter'
)
print(f"🖥️ Registered Code Interpreter tool")
```

### Phase 3: Inject Tool Usage Events into Stream

#### Approach A: Hook-based (Advanced)

```python
from strands.hooks import HookProvider, HookRegistry, BeforeInvocationEvent
from datetime import datetime
import json

class MCPToolHooks(HookProvider):
    def __init__(self, tool_tracker: MCPToolTracker):
        self.tool_tracker = tool_tracker
        
    def before_tool_invocation(self, event: BeforeInvocationEvent):
        """Hook called before tool invocation"""
        tool_info = self.tool_tracker.get_tool_info(event.tool_name)
        
        # Emit special event for frontend
        tool_event = {
            'type': 'tool_invocation',
            'tool_name': event.tool_name,
            'mcp_server': tool_info['mcp_name'],
            'mcp_url': tool_info['mcp_url'],
            'server_type': tool_info['server_type'],
            'timestamp': datetime.now().isoformat()
        }
        
        # This would need to be yielded through the streaming mechanism
        yield tool_event

    def register_hooks(self, registry: HookRegistry):
        """Register hooks with the agent"""
        registry.register_before_invocation(self.before_tool_invocation)
```

#### Approach B: Wrapper Functions (Simpler - Recommended)

```python
import json
from strands import tool

def create_tracked_tool(original_tool, tool_info):
    """
    Wrap MCP tool with tracking capabilities
    
    Args:
        original_tool: The original tool function
        tool_info: Information about the MCP server
    
    Returns:
        Wrapped tool that emits tracking events
    """
    @tool
    def tracked_tool(*args, **kwargs):
        # Emit tool usage event that will be captured by extract_text_from_event
        tool_event = {
            'type': 'tool_invocation',
            'tool_name': getattr(original_tool, 'name', original_tool.__name__),
            'mcp_server': tool_info['mcp_name'],
            'mcp_url': tool_info['mcp_url'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Print special marker that can be captured
        print(f"🔧 MCP_TOOL_USE: {json.dumps(tool_event)}")
        
        # Call original tool
        result = original_tool(*args, **kwargs)
        
        # Print completion marker
        print(f"✅ MCP_TOOL_COMPLETE: {tool_event['tool_name']}")
        
        return result
    
    # Preserve tool metadata
    tracked_tool.__name__ = original_tool.__name__
    tracked_tool.name = getattr(original_tool, 'name', original_tool.__name__)
    tracked_tool.description = getattr(original_tool, 'description', '')
    
    return tracked_tool

# Apply wrapper to tools when combining them
def wrap_tools_with_tracking(tools, mcp_name, mcp_url):
    """Wrap a list of tools with tracking"""
    tracked_tools = []
    for tool in tools:
        tool_info = {
            'mcp_name': mcp_name,
            'mcp_url': mcp_url,
            'server_type': 'bedrock-agentcore-runtime'
        }
        tracked_tool = create_tracked_tool(tool, tool_info)
        tracked_tools.append(tracked_tool)
    return tracked_tools
```

### Phase 4: Modify extract_text_from_event()

```python
def extract_text_from_event(event) -> str:
    """Extract text content from Strands streaming event structure"""
    if not event:
        return ""
    
    try:
        # Handle different event structures from Strands
        if isinstance(event, dict):
            # Check for tool invocation events (custom)
            if event.get('type') == 'tool_invocation':
                # Format tool usage message for frontend with special markers
                tool_msg = (
                    f"\n🔧 [MCP_TOOL_START] "
                    f"Tool: {event.get('tool_name', 'Unknown')} | "
                    f"Server: {event.get('mcp_server', 'Unknown')} | "
                    f"Type: {event.get('server_type', 'Unknown')}\n"
                )
                return tool_msg
            
            # ... rest of existing event handling code ...
            
        # ... rest of existing code ...
        
    except Exception as e:
        print(f"⚠️  Error extracting text from event: {e}")
        
    return ""
```

### Phase 5: Frontend Display Updates

#### 5.1 Update ChatInterface.tsx

```typescript
// Add to imports
import React, { useState, useEffect, useRef } from 'react';

// Add new interfaces
interface ToolUsage {
  toolName: string;
  mcpServer: string;
  serverType: string;
  timestamp: Date;
}

interface MessageWithTools extends ChatMessage {
  toolUsages?: ToolUsage[];
}

// Add tool usage tracking state
const [activeTools, setActiveTools] = useState<ToolUsage[]>([]);

// In the streaming callback handler
const handleStreamingChunk = (chunk: string) => {
  // Check for MCP tool markers
  const toolStartMatch = chunk.match(/\[MCP_TOOL_START\] Tool: (.*?) \| Server: (.*?) \| Type: (.*?)\n/);
  
  if (toolStartMatch) {
    const [, toolName, mcpServer, serverType] = toolStartMatch;
    const toolUsage: ToolUsage = {
      toolName,
      mcpServer,
      serverType,
      timestamp: new Date()
    };
    
    // Add to active tools
    setActiveTools(prev => [...prev, toolUsage]);
    
    // Remove the marker from the displayed text
    const cleanedChunk = chunk.replace(/\[MCP_TOOL_START\].*?\n/, '');
    
    // Add visual indicator to the message
    const indicator = createToolIndicator(toolUsage);
    return { text: cleanedChunk, indicator };
  }
  
  return { text: chunk, indicator: null };
};
```

#### 5.2 Add Visual Component for MCP Usage

```typescript
// Tool usage indicator component
const ToolUsageIndicator: React.FC<{ usage: ToolUsage }> = ({ usage }) => (
  <div className="tool-usage-indicator">
    <div className="tool-header">
      <span className="tool-icon">🔧</span>
      <span className="tool-status">Invoking Tool</span>
    </div>
    <div className="tool-details">
      <div className="tool-name">{usage.toolName}</div>
      <div className="mcp-info">
        <span className="mcp-badge">{usage.mcpServer}</span>
        <span className="server-type">
          {usage.serverType === 'bedrock-agentcore-runtime' 
            ? '⚡ Bedrock AgentCore Runtime' 
            : '💻 Local'}
        </span>
      </div>
    </div>
  </div>
);

// Active tools panel (optional - shows all currently executing tools)
const ActiveToolsPanel: React.FC<{ tools: ToolUsage[] }> = ({ tools }) => {
  if (tools.length === 0) return null;
  
  return (
    <div className="active-tools-panel">
      <h4>🚀 Active MCP Servers</h4>
      {tools.map((tool, index) => (
        <ToolUsageIndicator key={`${tool.toolName}-${index}`} usage={tool} />
      ))}
    </div>
  );
};
```

#### 5.3 Add Styles to App.css

```css
/* Tool usage indicator styles */
.tool-usage-indicator {
  display: inline-block;
  margin: 8px 0;
  padding: 8px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  font-size: 13px;
  animation: slideIn 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.tool-icon {
  font-size: 16px;
}

.tool-status {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.5px;
}

.tool-details {
  margin-left: 24px;
}

.tool-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.mcp-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  opacity: 0.95;
}

.mcp-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.server-type {
  font-size: 11px;
  opacity: 0.9;
}

/* Active tools panel */
.active-tools-panel {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 400px;
  overflow-y: auto;
}

.active-tools-panel h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

/* Animation */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Pulse animation for active tools */
.tool-usage-indicator.active {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.6);
  }
}
```

### Phase 6: Enhanced Backend Logging

Add detailed logging in strands_claude.py for debugging:

```python
def log_tool_invocation(tool_name: str, mcp_info: dict):
    """Log tool invocation details"""
    print(f"\n{'='*50}")
    print(f"🌐 MCP SERVER INVOCATION")
    print(f"{'='*50}")
    print(f"📍 Server: {mcp_info['mcp_name']}")
    print(f"🔗 Endpoint: {mcp_info['mcp_url']}")
    print(f"🔧 Tool: {tool_name}")
    print(f"⚡ Runtime: Bedrock AgentCore")
    print(f"🕒 Time: {datetime.now().isoformat()}")
    print(f"{'='*50}\n")
```

## Testing Plan

### 1. Unit Tests
- Test tool tracker registration
- Test tool info retrieval
- Test event extraction

### 2. Integration Tests
- **AWS Documentation Query**: "What is AWS Lambda?"
  - Expected: Shows "AWS Documentation MCP" indicator
- **Data Query**: "How many people watched movies in the last 2 hours?"
  - Expected: Shows "Data Processing MCP" indicator
- **Visualization Request**: "Create a bar chart of viewing statistics"
  - Expected: Shows "Code Interpreter (local)" indicator

### 3. End-to-End Tests
- Multiple tool calls in sequence
- Verify streaming doesn't break
- Check visual indicators appear correctly
- Ensure performance isn't degraded

### 4. Test Commands
```bash
# Test locally
cd backend/agent
python strands_claude.py '{"prompt": "What is AWS S3?"}'

# Test with streaming
python strands_claude.py '{"prompt": "Show me a chart of data", "streaming": true}'
```

## Benefits

1. **Transparency**: Users see which MCP servers are being utilized in real-time
2. **Debugging**: Easier to trace which service handles each request
3. **Demo Value**: Showcases the multi-MCP architecture effectively
4. **Real-time Feedback**: Immediate visibility of tool usage
5. **Educational**: Helps users understand the distributed architecture

## Alternative Implementation: Server-Sent Events (SSE)

Instead of text markers, use proper SSE format:

```python
# Backend: Yield SSE formatted events
def format_sse_event(event_type: str, data: dict) -> str:
    """Format data as SSE event"""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

# In streaming:
yield format_sse_event('tool_use', tool_info)
yield format_sse_event('message', {'text': response_text})
```

```typescript
// Frontend: Parse SSE events
const eventSource = new EventSource(url);
eventSource.addEventListener('tool_use', (e) => {
  const toolInfo = JSON.parse(e.data);
  addToolIndicator(toolInfo);
});
```

## Files to Modify

### Backend
1. **Create**: `backend/agent/mcp_tool_tracker.py` - New tool tracking module
2. **Modify**: `backend/agent/strands_claude.py` - Integrate tool tracking
3. **Copy to Deployment**: `backend/deployment/mcp_tool_tracker.py`
4. **Copy to Deployment**: Updated `backend/deployment/strands_claude.py`

### Frontend
1. **Modify**: `frontend/acme-chat/src/components/ChatInterface.tsx` - Add tool indicators
2. **Modify**: `frontend/acme-chat/src/App.css` - Style tool indicators

## Deployment Steps

### 1. Backend Deployment
```bash
# Copy updated files to deployment directory
cd backend/deployment
cp ../agent/strands_claude.py .
cp ../agent/mcp_tool_tracker.py .
cp ../agent/memory_manager.py .
cp ../agent/requirements.txt .

# Deploy agent
source .venv/bin/activate
python deploy_agent_with_auth.py
```

### 2. Frontend Deployment
```bash
# Build and deploy frontend
cd frontend/acme-chat
npm run build

cd ../infrastructure
npm run deploy
```

### 3. Verification
```bash
# Check agent logs
aws logs tail /aws/bedrock-agentcore/runtimes/strands_claude_getting_started_auth-nYQSK477I1-DEFAULT --region eu-central-1 --since 5m

# Test the deployment
curl -X POST https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/[AGENT_ARN]/invocations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt": "What is AWS Lambda?"}'
```

## Rollback Plan

If issues occur:
```bash
# Restore from backup
cp -r backup/backup_20250825_150928_pre_mcp_streaming/backend .
cp -r backup/backup_20250825_150928_pre_mcp_streaming/frontend .

# Redeploy original version
cd backend/deployment
python deploy_agent_with_auth.py
```

## Future Enhancements

1. **Tool Execution Time**: Show how long each tool takes
2. **Tool Success/Failure Status**: Indicate if tool execution succeeded
3. **Tool Input/Output Preview**: Show snippets of tool inputs/outputs
4. **MCP Server Health Status**: Display server availability
5. **Tool Usage Analytics**: Track and display tool usage statistics
6. **Caching Indicators**: Show when results are from cache vs fresh

---

**Document Version**: 1.0  
**Created**: 2025-08-25  
**Status**: Planning Phase