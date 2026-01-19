#!/usr/bin/env python3
"""
Test script to verify code_session functionality
"""

import json
import sys
import traceback
from bedrock_agentcore.tools.code_interpreter_client import code_session

def test_simple_code_session():
    """Test basic code execution with code_session"""
    print("🧪 Testing simple code_session execution...")
    
    simple_code = """
print("Hello from Code Interpreter!")
result = 2 + 2
print(f"2 + 2 = {result}")
    """
    
    try:
        print("📋 Code to execute:")
        print(simple_code)
        print("\n🔄 Executing with code_session...")
        
        with code_session("eu-central-1") as code_client:
            print("✅ code_session context manager created successfully")
            
            response = code_client.invoke("executeCode", {
                "code": simple_code,
                "language": "python",
                "clearContext": False
            })
            
            print("✅ code_client.invoke() called successfully")
            print(f"📄 Response type: {type(response)}")
            print(f"📄 Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            
            # Process the streaming response
            print("\n📡 Processing streaming response...")
            for i, event in enumerate(response["stream"]):
                print(f"📦 Event #{i+1}: {event}")
                
                if "result" in event:
                    result = event["result"]
                    print(f"✅ Found result: {type(result)}")
                    print(f"📋 Result content: {json.dumps(result, indent=2)}")
                    
                    # Check different response structures
                    if isinstance(result, dict):
                        print("\n🔍 Analyzing result structure:")
                        
                        # Check structuredContent.stdout
                        structured = result.get("structuredContent", {})
                        if structured and isinstance(structured, dict):
                            stdout = structured.get("stdout", "")
                            print(f"📤 structuredContent.stdout: {repr(stdout)}")
                        
                        # Check content[0].text
                        content = result.get("content", [])
                        if content and isinstance(content, list) and len(content) > 0:
                            content_text = content[0].get("text", "") if isinstance(content[0], dict) else ""
                            print(f"📤 content[0].text: {repr(content_text)}")
                        
                        # Check generic output field
                        output = result.get("output", "")
                        print(f"📤 output: {repr(output)}")
                        
                        # Check for any other text fields
                        for key, value in result.items():
                            if isinstance(value, str) and value.strip():
                                print(f"📤 {key}: {repr(value)}")
                
    except Exception as e:
        print(f"❌ Error during code execution: {e}")
        print(f"🔍 Exception type: {type(e)}")
        print(f"🔍 Traceback:")
        traceback.print_exc()
        return False
    
    print("✅ Simple code execution test completed")
    return True


def test_visualization_code_session():
    """Test visualization code execution similar to our agent"""
    print("\n🎨 Testing visualization code_session execution...")
    
    visualization_code = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

# Simple test data
data = [('A', 10), ('B', 20), ('C', 15)]
labels = [item[0] for item in data]
values = [item[1] for item in data]

# Create plot
plt.figure(figsize=(8, 6))
plt.bar(labels, values)
plt.title('Test Chart')
plt.xlabel('Categories')
plt.ylabel('Values')

# Save to base64
if plt.get_fignums():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close('all')
    print(f"IMAGE_DATA:{image_base64[:50]}...")  # Truncated for display
else:
    print("No figures to save")
    """
    
    try:
        print("📋 Visualization code to execute (truncated):")
        print(visualization_code[:300] + "...")
        print("\n🔄 Executing with code_session...")
        
        with code_session("eu-central-1") as code_client:
            response = code_client.invoke("executeCode", {
                "code": visualization_code,
                "language": "python",
                "clearContext": False
            })
            
            # Process response looking for IMAGE_DATA
            print("\n📡 Processing response for IMAGE_DATA...")
            found_image = False
            
            for i, event in enumerate(response["stream"]):
                if "result" in event:
                    result = event["result"]
                    
                    # Check all possible output locations
                    outputs_to_check = []
                    
                    if isinstance(result, dict):
                        # structuredContent.stdout
                        structured = result.get("structuredContent", {})
                        if isinstance(structured, dict):
                            outputs_to_check.append(("structuredContent.stdout", structured.get("stdout", "")))
                        
                        # content[0].text
                        content = result.get("content", [])
                        if content and isinstance(content, list) and len(content) > 0:
                            content_item = content[0] if isinstance(content[0], dict) else {}
                            outputs_to_check.append(("content[0].text", content_item.get("text", "")))
                        
                        # generic output
                        outputs_to_check.append(("output", result.get("output", "")))
                    
                    # Look for IMAGE_DATA in all outputs
                    for output_name, output_text in outputs_to_check:
                        if output_text and "IMAGE_DATA:" in str(output_text):
                            print(f"🎯 Found IMAGE_DATA in {output_name}!")
                            image_start = str(output_text).find("IMAGE_DATA:") + 11
                            image_preview = str(output_text)[image_start:image_start+50]
                            print(f"🖼️  Image data preview: {image_preview}...")
                            found_image = True
                            break
                
                if found_image:
                    break
            
            if not found_image:
                print("❌ No IMAGE_DATA found in response")
                
    except Exception as e:
        print(f"❌ Error during visualization test: {e}")
        traceback.print_exc()
        return False
    
    print("✅ Visualization test completed")
    return True


if __name__ == "__main__":
    print("🚀 Starting code_session tests...\n")
    
    # Test 1: Simple execution
    success1 = test_simple_code_session()
    
    # Test 2: Visualization
    success2 = test_visualization_code_session()
    
    print(f"\n📊 Test Results:")
    print(f"✅ Simple execution: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ Visualization: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)