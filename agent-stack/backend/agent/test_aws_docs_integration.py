#!/usr/bin/env python3
"""
Test script for AWS Documentation MCP integration
"""

import json
import sys
import os

def test_secrets_manager():
    """Test secrets manager integration"""
    try:
        print("🧪 Testing Secrets Manager integration...")
        from secrets_manager import secrets_manager
        
        # Test secret retrieval (will fail without actual secret)
        try:
            credentials = secrets_manager.get_mcp_credentials()
            print("✅ Secrets Manager integration working")
            return True
        except Exception as e:
            if "ResourceNotFoundException" in str(e):
                print("⚠️  Secret 'acme-chatbot/mcp-credentials' not found in AWS Secrets Manager")
                print("ℹ️  Create the secret first for full integration testing")
            else:
                print(f"❌ Secrets Manager error: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import secrets_manager: {e}")
        return False

def test_aws_docs_tools():
    """Test AWS documentation tools integration"""
    try:
        print("🧪 Testing AWS Documentation tools...")
        from aws_docs_tools import get_aws_docs_tools
        
        # Get tools (will return empty list if secrets not available)
        tools = get_aws_docs_tools()
        
        if tools:
            tool_names = [getattr(tool, '__name__', 'Unknown') for tool in tools]
            print(f"✅ AWS Documentation tools loaded: {tool_names}")
            return True
        else:
            print("⚠️  No AWS Documentation tools available (secrets not configured)")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import aws_docs_tools: {e}")
        return False

def test_agent_integration():
    """Test full agent integration"""
    try:
        print("🧪 Testing Agent integration...")
        from strands_claude import create_agent_with_memory
        
        # Create test payload
        test_payload = {
            "prompt": "Hello, test message",
            "sessionId": "test-session-123456789012345678901234567890123",
            "actorId": "test-user@acmecorp.com"
        }
        
        # Create agent (memory will fail without proper AWS setup)
        agent, memory_hooks = create_agent_with_memory(test_payload)
        
        if agent:
            print("✅ Agent created successfully")
            
            # Test basic functionality
            try:
                response = agent("What is 2+2?")
                result = response.message['content'][0]['text']
                print(f"✅ Agent response test: {result[:100]}...")
                return True
            except Exception as e:
                print(f"⚠️  Agent response test failed: {e}")
                return False
        else:
            print("❌ Failed to create agent")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import agent components: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting AWS Documentation MCP Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Secrets Manager
    results.append(("Secrets Manager", test_secrets_manager()))
    
    # Test 2: AWS Docs Tools
    results.append(("AWS Docs Tools", test_aws_docs_tools()))
    
    # Test 3: Agent Integration
    results.append(("Agent Integration", test_agent_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:<20}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Integration is ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Check configuration:")
        print("   1. Create AWS secret: acme-chatbot/mcp-credentials")
        print("   2. Update IAM role with Secrets Manager permissions")
        print("   3. Ensure MCP credentials are valid")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)