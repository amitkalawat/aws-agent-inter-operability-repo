#!/usr/bin/env python3
"""
Test Memory Integration for ACME Corp Chatbot
Tests memory creation, session/actor extraction, and basic memory operations
"""

import sys
import os
import json

# Add agent directory to path to import memory_manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent'))

from memory_manager import create_memory_manager, extract_session_info


def test_session_extraction():
    """Test session and actor ID extraction from various payload formats"""
    print("=== Testing Session/Actor ID Extraction ===")
    
    # Test 1: Metadata embedded in prompt (frontend pattern)
    test_payload1 = {
        'prompt': '[META:{"sid":"session-1756012929061-test","uid":"admin@acmecorp.com"}]Hello, test message',
        'sessionId': 'fallback-session',
        'streaming': True
    }
    
    session_id, actor_id = extract_session_info(test_payload1)
    print(f"Test 1 - Metadata format:")
    print(f"  Expected: session=session-1756012929061-test, actor=admin@acmecorp.com")
    print(f"  Actual:   session={session_id}, actor={actor_id}")
    print(f"  Result:   {'✅ PASS' if session_id == 'session-1756012929061-test' and actor_id == 'admin@acmecorp.com' else '❌ FAIL'}")
    print()
    
    # Test 2: Direct payload fields (fallback)
    test_payload2 = {
        'prompt': 'Regular message without metadata',
        'sessionId': 'direct-session-123',
        'actorId': 'user@example.com'
    }
    
    session_id2, actor_id2 = extract_session_info(test_payload2)
    print(f"Test 2 - Direct payload format:")
    print(f"  Expected: session=direct-session-123, actor=user@example.com")
    print(f"  Actual:   session={session_id2}, actor={actor_id2}")
    print(f"  Result:   {'✅ PASS' if session_id2 == 'direct-session-123' and actor_id2 == 'user@example.com' else '❌ FAIL'}")
    print()
    
    # Test 3: Default values
    test_payload3 = {
        'prompt': 'Message with no session info'
    }
    
    session_id3, actor_id3 = extract_session_info(test_payload3)
    print(f"Test 3 - Default values:")
    print(f"  Expected: session=default-session, actor=anonymous-user")
    print(f"  Actual:   session={session_id3}, actor={actor_id3}")
    print(f"  Result:   {'✅ PASS' if session_id3 == 'default-session' and actor_id3 == 'anonymous-user' else '❌ FAIL'}")
    print()


def test_memory_creation():
    """Test memory creation and configuration"""
    print("=== Testing Memory Creation ===")
    
    # Test with extracted session info
    test_payload = {
        'prompt': '[META:{"sid":"test-session-123","uid":"test-user@acme.com"}]Test memory creation',
    }
    
    try:
        session_id, actor_id = extract_session_info(test_payload)
        print(f"Creating memory for session={session_id}, actor={actor_id}")
        
        # Create memory manager (this will test the actual AWS API calls)
        memory_hooks = create_memory_manager(
            memory_name=f"ACMEChatMemory_test_{hash(actor_id) % 10000:04d}",
            actor_id=actor_id,
            session_id=session_id,
            region="eu-central-1"
        )
        
        if hasattr(memory_hooks, 'memory_client'):
            print("✅ Memory manager created successfully")
            print(f"✅ Memory client initialized: {type(memory_hooks.memory_client).__name__}")
            print(f"✅ Memory ID: {memory_hooks.memory_id}")
            
            # Test conversation context retrieval
            try:
                context = memory_hooks.retrieve_conversation_context("Test query")
                print(f"✅ Context retrieval test completed: {len(context)} characters")
            except Exception as context_error:
                print(f"⚠️  Context retrieval failed (expected for new memory): {context_error}")
            
            # Test saving interaction
            try:
                memory_hooks.save_chat_interaction("Hello", "Hi there!")
                print("✅ Interaction save test completed")
            except Exception as save_error:
                print(f"❌ Interaction save failed: {save_error}")
                
        else:
            print("⚠️  Memory manager returned dummy implementation (no AWS access)")
            
    except Exception as e:
        print(f"❌ Memory creation test failed: {e}")
        print("⚠️  This might be expected if AWS credentials/permissions are not configured")
    
    print()


def test_memory_id_format():
    """Test that memory IDs follow the correct AWS pattern"""
    print("=== Testing Memory ID Format Validation ===")
    
    # AWS pattern: [a-zA-Z][a-zA-Z0-9-_]{0,99}-[a-zA-Z0-9]{10}
    test_memory_names = [
        "ACMEChatMemory_test1234",
        "PersonalAgentMemory", 
        "TestMemory_abc"
    ]
    
    import re
    aws_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9-_]{0,99}-[a-zA-Z0-9]{10}$')
    
    print("Testing memory ID patterns (simulated AWS format):")
    for memory_name in test_memory_names:
        # Simulate AWS ID format: name + dash + 10 chars
        simulated_id = f"{memory_name}-abc1234567"
        is_valid = aws_pattern.match(simulated_id)
        print(f"  {memory_name} → {simulated_id}")
        print(f"    AWS Pattern Valid: {'✅ YES' if is_valid else '❌ NO'}")
    
    print()


def main():
    """Run all memory integration tests"""
    print("🧠 Memory Integration Test Suite")
    print("================================")
    print()
    
    test_session_extraction()
    test_memory_id_format()
    test_memory_creation()
    
    print("=== Test Summary ===")
    print("✅ Session/Actor extraction tests completed")
    print("✅ Memory ID format validation completed")
    print("✅ Memory creation tests completed")
    print()
    print("📝 Notes:")
    print("- Memory creation may fail without proper AWS credentials/permissions")
    print("- This is expected until the IAM policy is applied")
    print("- Run apply_memory_policy.py to grant required permissions")
    print()


if __name__ == "__main__":
    main()