#!/usr/bin/env python3
"""
Test script to verify both AWS Documentation and DataProcessing MCP clients
"""

import sys
sys.path.append('.')

from strands_claude import mcp_manager

def test_mcp_clients():
    """Test both MCP clients with OAuth authentication"""
    
    print("🧪 Testing MCP Client Authentication")
    print("="*50)
    
    # Test AWS Documentation MCP
    print("\n1. Testing AWS Documentation MCP...")
    try:
        aws_docs_client = mcp_manager.create_aws_docs_client()
        print("   ✅ AWS Documentation MCP client created successfully")
        
        with aws_docs_client:
            tools = aws_docs_client.list_tools_sync()
            print(f"   ✅ Found {len(tools)} AWS docs tools")
            for tool in tools[:3]:  # Show first 3 tools
                print(f"      - {tool.name}")
    except Exception as e:
        print(f"   ❌ AWS Documentation MCP failed: {e}")
    
    # Test DataProcessing MCP
    print("\n2. Testing DataProcessing MCP...")
    try:
        dataproc_client = mcp_manager.create_dataproc_client()
        print("   ✅ DataProcessing MCP client created successfully")
        
        with dataproc_client:
            tools = dataproc_client.list_tools_sync()
            print(f"   ✅ Found {len(tools)} dataproc tools")
            for tool in tools[:3]:  # Show first 3 tools
                print(f"      - {tool.name}")
    except Exception as e:
        print(f"   ❌ DataProcessing MCP failed: {e}")
    
    print("\n🏁 MCP Authentication Test Complete")

if __name__ == "__main__":
    test_mcp_clients()