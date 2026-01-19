#!/usr/bin/env python3
"""
Demonstrate the MCP context manager issue
"""

print("🔍 MCP Context Manager Issue Analysis")
print("=" * 60)

print("\n❌ CURRENT BROKEN APPROACH:")
print("def get_aws_docs_tools():")
print("    client = get_aws_docs_mcp_client()")
print("    with client:")
print("        tools = client.list_tools_sync()  # Tools created in context")
print("        return tools  # Tools returned outside context")
print("")
print("# Later when Agent tries to use tools...")
print("agent = Agent(model=model, tools=aws_docs_tools)  # FAILS!")
print("# Error: client session is not running")

print("\n✅ SOLUTION - RETURN CLIENT AND TOOLS TOGETHER:")
print("def get_aws_docs_mcp_client_and_tools():")
print("    client = get_aws_docs_mcp_client()")
print("    if client is None:")
print("        return None, []")
print("    return client, client.list_tools_sync()")
print("")
print("# In agent creation:")
print("mcp_client, aws_tools = get_aws_docs_mcp_client_and_tools()")
print("with mcp_client:")
print("    agent = Agent(model=model, tools=calculator + weather + aws_tools)")

print("\n🔧 The fix requires refactoring how we manage the MCP client lifecycle")
print("💡 We need to keep the client alive throughout the agent's lifetime")

print("\n" + "=" * 60)