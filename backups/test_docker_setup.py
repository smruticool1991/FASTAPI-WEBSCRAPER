#!/usr/bin/env python3
"""
Test script to verify Docker setup is working correctly
Run this after starting the Docker containers
"""

import requests
import time
import json

def test_docker_api():
    """Test the Docker-deployed API"""
    
    print("🐳 Testing Docker-deployed Website Analysis API")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health check failed: {e}")
        print("   🔧 Make sure Docker containers are running:")
        print("       ./docker-run.sh dev")
        return False
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ Root endpoint accessible")
            data = response.json()
            print(f"   API Name: {data.get('name', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")
        else:
            print(f"   ❌ Root endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Root endpoint failed: {e}")
    
    # Test 3: API documentation
    print("\n3. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("   ✅ API documentation accessible")
            print(f"   Documentation available at: {base_url}/docs")
        else:
            print(f"   ❌ Documentation failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Documentation failed: {e}")
    
    # Test 4: Actual website analysis
    print("\n4. Testing website analysis...")
    test_payload = {
        "domains": ["httpbin.org"],
        "batch_size": 1,
        "timeout": 30
    }
    
    try:
        print("   Sending request to analyze httpbin.org...")
        response = requests.post(
            f"{base_url}/analyze",
            json=test_payload,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                print("   ✅ Website analysis successful")
                print(f"   Domain: {result.get('domain', 'Unknown')}")
                print(f"   Status: {result.get('status', 'Unknown')}")
                print(f"   Platform: {result.get('platform', 'Unknown')}")
                print(f"   Emails found: {len(result.get('emails', []))}")
                if result.get('emails'):
                    print(f"   Email: {result['emails'][0]}")
                print(f"   SEO Score: {result.get('seoScore', 0)}/100")
            else:
                print("   ❌ Empty response received")
        else:
            print(f"   ❌ Analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Analysis request failed: {e}")
    
    print(f"\n{'=' * 50}")
    print("🎉 Docker API test completed!")
    print(f"\nIf all tests passed, your Docker deployment is working correctly!")
    print(f"🌐 API URL: {base_url}")
    print(f"📚 Documentation: {base_url}/docs")
    print(f"❤️  Health Check: {base_url}/health")
    
    return True

def test_production_endpoints():
    """Test production-specific endpoints if available"""
    
    production_endpoints = {
        "Prometheus": "http://localhost:9090",
        "Grafana": "http://localhost:3000", 
        "Database": "localhost:5432",
        "Redis": "localhost:6379"
    }
    
    print(f"\n{'=' * 50}")
    print("🏭 Testing production endpoints...")
    
    for name, url in production_endpoints.items():
        if name in ["Database", "Redis"]:
            print(f"   {name}: {url} (connection test skipped)")
            continue
            
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name}: {url}")
            else:
                print(f"   ⚠️  {name}: {url} ({response.status_code})")
        except requests.exceptions.RequestException:
            print(f"   ❌ {name}: {url} (not accessible)")

if __name__ == "__main__":
    print("Docker API Test Script")
    print("Make sure to start Docker containers first:")
    print("  ./docker-run.sh dev   (for development)")
    print("  ./docker-run.sh prod  (for production)")
    print()
    
    # Wait a moment for containers to be ready
    print("Waiting 3 seconds for containers to be ready...")
    time.sleep(3)
    
    # Run main API tests
    test_docker_api()
    
    # Test production endpoints if they might be running
    test_production_endpoints()
    
    print(f"\n🐳 Docker deployment test completed!")
    print(f"For container status: ./docker-run.sh status")
    print(f"For container logs: ./docker-run.sh logs")