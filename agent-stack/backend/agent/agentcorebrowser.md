# AgentCore Browser Integration Plan

## Overview
This document outlines the plan to add browser automation capabilities to the ACME Corp Bedrock AgentCore chatbot using AWS's AgentCoreBrowser tool from the strands_tools package.

## AWS Official AgentCore Browser Tool

### Service Announcement
- **Announced**: AWS Summit New York City 2025
- **Status**: Preview Release (subject to change)
- **Description**: Fully managed, pre-built cloud-based browser that enables generative AI agents to interact seamlessly with websites

### Key Differentiators
- **Managed Infrastructure**: No browser infrastructure to maintain
- **Session Isolation**: Complete isolation prevents data leakage between sessions
- **Built-in Security**: CloudTrail logging, session replay, containerized environment
- **Scalable**: Handles both low-latency real-time and 8-hour asynchronous workloads
- **Framework Agnostic**: Works with CrewAI, LangGraph, LlamaIndex, Strands Agents, and any foundation model

### Architecture & Infrastructure
- **Environment**: Containerized, serverless cloud-based browser infrastructure
- **Communication**: WebSocket-based connections with headers authentication
- **Session Management**: Ephemeral sessions with automatic timeouts
- **Isolation**: Complete session isolation in containerized environment
- **Workload Types**: 
  - Low-latency real-time iterations
  - Long-running asynchronous tasks (up to 8 hours)

### Official Use Cases
1. **Repetitive Web Tasks at Scale**
   - Populate complex web forms across multiple systems
   - Validate entries and maintain compliance with business rules
   - Automate data entry workflows

2. **Dashboard Monitoring & Reporting**
   - Navigate to internal dashboards automatically
   - Extract critical metrics without human intervention
   - Compile automated reports from web interfaces

3. **Research & Intelligence Gathering**
   - Track websites for pricing changes automatically
   - Monitor new product launches and content updates
   - Gather competitive intelligence at scale

4. **Web Scraping & Data Extraction**
   - Extract data from multiple sources simultaneously
   - Handle dynamic content and JavaScript-heavy sites
   - Scale web data collection operations

## Current State Analysis

### Existing Infrastructure
- **Framework**: Strands Agent with Bedrock AgentCore runtime
- **Model**: Claude 3.7 Sonnet (`eu.anthropic.claude-3-7-sonnet-20250219-v1:0`)
- **Region**: eu-central-1
- **Tools**: MCP tools (AWS docs, data processing), Code Interpreter
- **Dependencies**: `strands-agents` and `strands-agents-tools` already installed

### Missing Components
- `playwright` package (required for browser automation)
- Playwright browser binaries (Chromium)
- Browser tool integration code

## Availability & Pricing

### Preview Regions
Currently available in preview in the following AWS regions:
- **US East (N. Virginia)** - us-east-1
- **US West (Oregon)** - us-west-2  
- **Asia Pacific (Sydney)** - ap-southeast-2
- **Europe (Frankfurt)** - eu-central-1 ⭐ *Our deployment region*

### Pricing Model
- **Free Trial Period**: Until September 16, 2025
- **Billing Method**: Per-second billing based on CPU and memory usage watermark
- **Minimum Charges**: 1-second minimum billing increment
- **Cost Structure**: No upfront commitments or minimum fees
- **Payment Model**: Pay only for actual usage (consumption-based)

### Access Methods
- AWS Management Console
- AWS CLI
- AWS SDKs  
- AgentCore SDK (recommended for integration)

## Implementation Plan

### Phase 1: Dependencies Setup

#### 1.1 Update requirements.txt
Add the following to `backend/agent/requirements.txt`:
```
playwright
```

#### 1.2 Install Dependencies
```bash
cd backend/agent
source .venv/bin/activate
pip install playwright
playwright install chromium
```

#### 1.2a Alternative: Official AWS SDK Setup
```bash
# Official AWS recommended setup
git clone https://github.com/awslabs/amazon-bedrock-agentcore-samples.git
cd amazon-bedrock-agentcore-samples
pip install -r requirements.txt
pip install playwright
```

#### 1.3 Verify Installation
```python
from strands_tools.browser import AgentCoreBrowser
print("AgentCoreBrowser successfully imported")
```

### Phase 2: Browser Tool Module Creation

#### 2.1 Create browser_tool.py
Location: `backend/agent/browser_tool.py`

```python
"""
Browser Tool Integration for ACME Corp Chatbot
Provides web browsing and automation capabilities using AgentCoreBrowser
"""

from typing import Optional
import os

def create_browser_tool(region: str = None) -> Optional[object]:
    """
    Create and configure AgentCoreBrowser tool
    
    Args:
        region: AWS region for browser service (defaults to EU_CENTRAL_1)
    
    Returns:
        Browser tool instance or None if unavailable
    """
    try:
        from strands_tools.browser import AgentCoreBrowser
        
        # Use environment variable or default region
        if region is None:
            region = os.environ.get('AWS_REGION', 'eu-central-1')
        
        print(f"🌐 Initializing AgentCoreBrowser in region: {region}")
        agent_core_browser = AgentCoreBrowser(region=region)
        
        print("✅ Browser tool initialized successfully")
        return agent_core_browser.browser
        
    except ImportError as e:
        print(f"⚠️  Browser tool not available - missing dependency: {e}")
        return None
    except Exception as e:
        print(f"❌ Failed to initialize browser tool: {e}")
        return None

def get_browser_capabilities() -> str:
    """
    Return description of browser capabilities for system prompt
    """
    return """
Browser Automation Capabilities:
- Search and navigate websites programmatically
- Extract information from web pages
- Fill forms and interact with page elements
- Take screenshots of web pages
- Search for products on e-commerce sites
- Compare prices and features across websites
- Access real-time web content and data
- Perform automated web research
"""
```

### Phase 3: Main Agent Integration

#### 3.1 Update strands_claude.py

**Import Section (around line 25):**
```python
from browser_tool import create_browser_tool, get_browser_capabilities
```

**Global Browser Tool (around line 200):**
```python
# Browser tool configuration
BROWSER_REGION = 'eu-central-1'
browser_tool = create_browser_tool(BROWSER_REGION)
```

**System Prompt Update (around line 440):**
Add browser capabilities to the base prompt:
```python
# Add browser capabilities if available
browser_info = ""
if browser_tool:
    browser_info = f"\n\n{get_browser_capabilities()}"

base_prompt = f"""You're a helpful AI assistant powered by Claude for ACME Corp...
{existing_content}
{browser_info}
"""
```

**Tool Integration - Non-Streaming (around line 609):**
```python
# Combine tools from all sources
all_tools = aws_tools + dataproc_tools + [execute_code_with_visualization]

# Add browser tool if available
if browser_tool:
    all_tools.append(browser_tool)
    print("🌐 Browser tool added to agent capabilities")
```

**Tool Integration - Streaming (around line 708):**
```python
# Combine tools from all sources
all_tools = aws_tools + dataproc_tools + [execute_code_with_visualization]

# Add browser tool if available
if browser_tool:
    all_tools.append(browser_tool)
    print("🌐 Browser tool added to streaming agent capabilities")
```

### Phase 4: Deployment Updates

#### 4.1 Update Deployment requirements.txt
Sync `backend/deployment/requirements.txt` with agent requirements:
```
playwright
```

#### 4.2 Dockerfile Considerations
If using Docker, add playwright installation:
```dockerfile
# Install playwright and browsers
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps chromium
```

#### 4.3 Container Resource Limits
Browser automation requires more resources:
- Memory: Increase to at least 2GB
- CPU: Consider 1-2 vCPUs minimum
- Storage: Add ~500MB for browser binaries

### Phase 5: Testing

#### 5.1 Local Testing Script
Create `test_browser.py`:
```python
#!/usr/bin/env python3
import json
from strands_claude import strands_agent_bedrock

# Test browser search
test_prompts = [
    "Search for coffee makers on amazon.com and tell me about the first result",
    "Go to python.org and tell me what's on the homepage",
    "Search Google for 'AWS Bedrock AgentCore' and summarize the top results"
]

for prompt in test_prompts:
    print(f"\nTesting: {prompt}")
    response = strands_agent_bedrock({"prompt": prompt})
    print(f"Response: {response[:200]}...")
```

#### 5.2 Integration Tests
1. **Basic Import Test**: Verify AgentCoreBrowser imports correctly
2. **Tool Creation Test**: Ensure browser tool initializes
3. **Agent Integration Test**: Confirm agent can use browser tool
4. **Web Navigation Test**: Test actual web browsing
5. **Error Handling Test**: Verify graceful failure when browser unavailable

### Phase 6: Usage Examples

#### Official AWS Example Code Patterns

**Playwright Integration (Official AWS Pattern):**
```python
from playwright.sync_api import sync_playwright, Playwright, BrowserType
from bedrock_agentcore.tools.browser_client import browser_session
from browser_viewer import BrowserViewerServer
import time

def run(playwright: Playwright):
    # Create browser session with AWS managed browser
    with browser_session('eu-central-1') as client:
        ws_url, headers = client.generate_ws_headers()
        
        # Start viewer server for monitoring (optional)
        viewer = BrowserViewerServer(client, port=8005)
        viewer_url = viewer.start(open_browser=True)
        
        # Connect using WebSocket with authentication headers
        chromium: BrowserType = playwright.chromium
        browser = chromium.connect_over_cdp(ws_url, headers=headers)
        
        context = browser.contexts[0]
        page = context.pages[0]
        
        try:
            # Navigate to target website
            page.goto("https://amazon.com/")
            print(f"Page title: {page.title()}")
            
            # Perform browser interactions
            # Your automation code here
            time.sleep(10)  # Allow time for manual observation
            
        finally:
            # Cleanup is handled by context manager
            pass

# Run with Playwright
with sync_playwright() as playwright:
    run(playwright)
```

**Strands Framework Integration (Our Implementation Pattern):**
```python
from strands_tools.browser import AgentCoreBrowser

def create_browser_agent():
    """Create agent with browser capabilities following AWS patterns"""
    agent_core_browser = AgentCoreBrowser(region="eu-central-1")
    return agent_core_browser.browser
```

#### Example Prompts
```python
# Product Search
"Find the best-rated coffee makers under $200 on Amazon"

# Price Comparison
"Compare prices for iPhone 15 Pro on Amazon, Best Buy, and Apple.com"

# Information Gathering
"What are the latest updates on the AWS Bedrock documentation page?"

# Form Interaction
"Go to the AWS console login page and describe what fields are required"

# Research Task
"Search for recent news about Claude 3 and summarize the top 5 articles"

# Official AWS Example Use Cases
"Navigate to internal dashboards and extract key performance metrics"
"Populate complex web forms across multiple enterprise systems"
"Monitor competitor pricing changes across e-commerce platforms"
```

## Troubleshooting

### Common Issues and Solutions

1. **ModuleNotFoundError: playwright**
   - Solution: `pip install playwright`

2. **Browser binary not found**
   - Solution: `playwright install chromium`

3. **Permission denied errors**
   - Solution: Ensure user has write permissions for browser cache

4. **Memory issues**
   - Solution: Increase container/instance memory limits

5. **Region mismatch**
   - Solution: Ensure BROWSER_REGION matches deployment region

## Security Considerations

### AWS Managed Security Features
1. **Complete Session Isolation**: Each browser session runs in isolated containers preventing data leakage
2. **CloudTrail Integration**: All browser actions are logged for audit and compliance
3. **Session Replay**: Built-in capability to replay sessions for debugging and analysis
4. **Ephemeral Sessions**: Automatic session cleanup and timeout management
5. **Containerized Environment**: Browser runs in secure, managed containers
6. **Built-in Observability**: Live viewing capabilities with security monitoring

### Implementation Security Best Practices
1. **Website Access**: Browser can access any public website - validate URLs
2. **Credentials**: Never store login credentials in code - use AWS Secrets Manager
3. **Rate Limiting**: Implement delays to avoid being blocked or flagged
4. **Robots.txt**: Respect website robots.txt policies and terms of service
5. **Data Privacy**: Be cautious with sensitive information extraction
6. **Network Security**: Ensure WebSocket connections are secure and authenticated
7. **Session Management**: Implement proper session cleanup and timeout handling

## Performance Optimization

1. **Browser Reuse**: Keep browser instance alive between requests
2. **Page Caching**: Cache frequently accessed pages
3. **Selective Loading**: Disable images/CSS when not needed
4. **Timeout Configuration**: Set appropriate timeouts for page loads
5. **Resource Cleanup**: Properly close browser sessions

## Monitoring and Observability

### AWS Built-in Monitoring
1. **Live View Stream**: Real-time monitoring of browser sessions with visual feedback
2. **Browser Viewer Server**: Built-in viewer server for debugging interactions
3. **CloudWatch Integration**: Automatic performance metrics tracking
4. **Session Recording**: Complete interaction history with replay capability
5. **CloudTrail Logging**: Comprehensive audit trail of all browser actions

### Custom Monitoring Implementation
1. **Browser Actions**: Log all navigation and interactions
2. **Performance Metrics**: Track page load times and response latencies
3. **Error Tracking**: Log and alert on browser failures and timeouts
4. **Usage Analytics**: Monitor which sites are accessed most frequently
5. **Resource Usage**: Track memory and CPU consumption patterns

### Official AWS Code Example for Monitoring
```python
from bedrock_agentcore.tools.browser_client import browser_session
from browser_viewer import BrowserViewerServer

def run_with_monitoring():
    with browser_session('eu-central-1') as client:
        ws_url, headers = client.generate_ws_headers()
        
        # Start built-in viewer server for live monitoring
        viewer = BrowserViewerServer(client, port=8005)
        viewer_url = viewer.start(open_browser=True)
        
        print(f"Browser session monitoring available at: {viewer_url}")
        
        # Your browser automation code here
        # All interactions will be visible in the viewer
```

## Future Enhancements

1. **Headless Mode Toggle**: Allow switching between headless and headed mode
2. **Screenshot Capabilities**: Add screenshot capture and storage
3. **Session Management**: Implement browser session persistence
4. **Proxy Support**: Add proxy configuration for geo-specific browsing
5. **Custom Scripts**: Allow injection of custom JavaScript
6. **Visual Debugging**: Integrate browser viewer server from AWS examples
7. **Multi-Browser Support**: Add Firefox and Safari support
8. **Cookie Management**: Implement cookie storage and retrieval

## Rollback Plan

If issues arise:
1. Set `browser_tool = None` to disable browser features
2. Remove browser tool from `all_tools` list
3. Revert system prompt changes
4. Uninstall playwright if needed

## Success Criteria

- ✅ Browser tool successfully imports and initializes
- ✅ Agent can navigate to websites and extract information
- ✅ No performance degradation for non-browser requests
- ✅ Error handling prevents crashes when browser unavailable
- ✅ Successfully deployed to production environment

## Timeline

1. **Day 1**: Dependencies installation and basic integration
2. **Day 2**: Testing and error handling implementation
3. **Day 3**: Deployment preparation and documentation
4. **Day 4**: Production deployment and monitoring
5. **Day 5**: Performance optimization and refinements

## Preview Release Considerations

### Important Limitations
- **Preview Status**: Currently in preview release, subject to changes before GA
- **Feature Stability**: APIs and interfaces may change without notice
- **Production Use**: Evaluate carefully for production workloads
- **Regional Availability**: Limited to specific preview regions

### Support and Feedback
- **Community Support**: AgentCore Preview Discord server for feedback and discussion
- **Documentation**: Subject to updates as service evolves
- **Bug Reports**: Use AWS support channels for technical issues
- **Feature Requests**: Submit through appropriate AWS feedback channels

## Additional Resources

### Official AWS Resources
- **Main Documentation**: [AWS Bedrock AgentCore Browser Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser-building-agents.html)
- **Getting Started Guide**: [Browser Tool Onboarding](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser-onboarding.html)
- **Sample Code Repository**: [amazon-bedrock-agentcore-samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
- **Blog Announcement**: [Introducing Amazon Bedrock AgentCore Browser Tool](https://aws.amazon.com/blogs/machine-learning/introducing-amazon-bedrock-agentcore-browser-tool/)
- **Service Overview**: [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
- **Pricing Information**: [AgentCore Pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)

### Technical References
- **Strands Tools Documentation**: [Strands Framework](https://github.com/strands/strands-tools)
- **Playwright Documentation**: [Python Playwright](https://playwright.dev/python/)
- **WebSocket Standards**: For understanding connection protocols
- **Docker Documentation**: For containerization concepts

### Community and Support
- **AgentCore Preview Discord**: Official community support channel
- **AWS Support Center**: For technical assistance
- **AWS Forums**: Community discussions and Q&A
- **GitHub Issues**: For SDK-related bug reports