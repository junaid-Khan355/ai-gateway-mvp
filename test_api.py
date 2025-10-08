#!/usr/bin/env python3
"""
Simple test script for the AI Gateway MVP
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"  # You'll need to create a user with this key first

def test_create_user():
    """Test user creation"""
    print("Testing user creation...")
    
    response = requests.post(
        f"{BASE_URL}/v1/users",
        json={
            "email": "test@example.com",
            "api_key": API_KEY
        }
    )
    
    if response.status_code == 200:
        print("✅ User created successfully")
        return True
    else:
        print(f"❌ User creation failed: {response.status_code} - {response.text}")
        return False

def test_list_models():
    """Test model listing"""
    print("Testing model listing...")
    
    response = requests.get(
        f"{BASE_URL}/v1/models",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    
    if response.status_code == 200:
        models = response.json()
        print(f"✅ Found {len(models['data'])} models")
        for model in models['data'][:3]:  # Show first 3 models
            print(f"   - {model['id']}")
        return True
    else:
        print(f"❌ Model listing failed: {response.status_code} - {response.text}")
        return False

def test_chat_completion():
    """Test chat completion"""
    print("Testing chat completion...")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": "Say hello in exactly 5 words."
                }
            ],
            "max_tokens": 50
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        usage = result['usage']
        print(f"✅ Chat completion successful")
        print(f"   Response: {content}")
        print(f"   Tokens: {usage['total_tokens']}")
        return True
    else:
        print(f"❌ Chat completion failed: {response.status_code} - {response.text}")
        return False

def test_embeddings():
    """Test embeddings"""
    print("Testing embeddings...")
    
    response = requests.post(
        f"{BASE_URL}/v1/embeddings",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/text-embedding-3-small",
            "input": "The quick brown fox jumps over the lazy dog"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        embedding = result['data'][0]['embedding']
        print(f"✅ Embeddings successful")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        return True
    else:
        print(f"❌ Embeddings failed: {response.status_code} - {response.text}")
        return False

def test_credits():
    """Test credits endpoint"""
    print("Testing credits...")
    
    response = requests.get(
        f"{BASE_URL}/v1/credits",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    
    if response.status_code == 200:
        credits = response.json()
        print(f"✅ Credits retrieved")
        print(f"   Balance: ${credits['balance']}")
        print(f"   Total Used: ${credits['total_used']}")
        return True
    else:
        print(f"❌ Credits failed: {response.status_code} - {response.text}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting AI Gateway MVP Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Server is not running. Please start the server first.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the server first.")
        return
    
    print("✅ Server is running")
    print()
    
    # Run tests
    tests = [
        test_create_user,
        test_list_models,
        test_chat_completion,
        test_embeddings,
        test_credits
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print()
    
    print("=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your AI Gateway MVP is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
