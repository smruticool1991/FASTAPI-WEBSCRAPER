#!/usr/bin/env python3
"""
Test script for email priority feature
Tests how different email priority settings affect the results
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_email_priority():
    """Test email priority functionality"""
    print("🎯 Testing Email Priority Feature")
    print("=" * 50)
    
    # Test domain (using a test case)
    test_domain = "httpbin.org"
    
    # Different priority configurations to test
    priority_configs = [
        {
            "name": "Default Priority",
            "email_priority": ["info@", "sales@", "@gmail.com"],
            "description": "Default: info@, sales@, @gmail.com"
        },
        {
            "name": "Contact First Priority",
            "email_priority": ["contact@", "support@", "@company.com"],
            "description": "Contact first: contact@, support@, @company.com"
        },
        {
            "name": "Gmail Priority", 
            "email_priority": ["@gmail.com", "@yahoo.com", "info@"],
            "description": "Gmail first: @gmail.com, @yahoo.com, info@"
        },
        {
            "name": "Business Domain Priority",
            "email_priority": ["@business.com", "@company.org", "admin@"],
            "description": "Business domains: @business.com, @company.org, admin@"
        },
        {
            "name": "Sales Focus",
            "email_priority": ["sales@", "business@", "marketing@"],
            "description": "Sales focus: sales@, business@, marketing@"
        }
    ]
    
    print(f"Testing with domain: {test_domain}")
    print(f"Testing {len(priority_configs)} different priority configurations\n")
    
    results = {}
    
    for config in priority_configs:
        print(f"Testing: {config['name']}")
        print(f"  Configuration: {config['description']}")
        
        # Prepare request payload
        payload = {
            "domains": [test_domain],
            "batch_size": 1,
            "timeout": 15,
            "email_priority": config["email_priority"]
        }
        
        try:
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/analyze",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    emails = result.get('emails', [])
                    
                    print(f"  ✅ Found {len(emails)} emails:")
                    for i, email in enumerate(emails, 1):
                        print(f"    {i}. {email}")
                    
                    results[config['name']] = {
                        'emails': emails,
                        'priority': config['email_priority'],
                        'count': len(emails)
                    }
                else:
                    print(f"  ❌ No results returned")
                    results[config['name']] = {'emails': [], 'count': 0}
            else:
                print(f"  ❌ API request failed: {response.status_code}")
                results[config['name']] = {'error': response.status_code}
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request failed: {e}")
            results[config['name']] = {'error': str(e)}
        
        print()  # Empty line between tests
        time.sleep(1)  # Small delay between requests
    
    # Summary
    print("=" * 50)
    print("EMAIL PRIORITY TEST SUMMARY")
    print("=" * 50)
    
    for config_name, result in results.items():
        if 'error' in result:
            print(f"❌ {config_name}: Failed ({result['error']})")
        else:
            email_count = result['count']
            emails = result.get('emails', [])
            print(f"✅ {config_name}: {email_count} emails")
            if emails:
                print(f"   Top email: {emails[0]}")
    
    return results

def test_priority_scoring():
    """Test the priority scoring logic with mock data"""
    print("\n🧪 Testing Priority Scoring Logic")
    print("=" * 50)
    
    # Mock emails for testing
    mock_emails = [
        "info@company.com",
        "sales@business.org", 
        "contact@website.net",
        "support@service.com",
        "john.doe@gmail.com",
        "admin@yahoo.com",
        "newsletter@marketing.com"
    ]
    
    priority_tests = [
        ["info@", "sales@", "@gmail.com"],
        ["contact@", "support@", "@yahoo.com"],
        ["@gmail.com", "@yahoo.com", "admin@"],
        ["sales@", "@business.org", "john.doe@"]
    ]
    
    print("Mock emails for testing:")
    for i, email in enumerate(mock_emails, 1):
        print(f"  {i}. {email}")
    
    print(f"\nTesting {len(priority_tests)} priority configurations:")
    
    for i, priority in enumerate(priority_tests, 1):
        print(f"\n{i}. Priority: {priority}")
        
        # Simple scoring simulation (would use actual API scoring in real test)
        scores = []
        for email in mock_emails:
            score = 100  # Base score
            username, domain = email.split('@')
            
            # Apply priority bonus
            for j, pattern in enumerate(priority):
                if pattern.startswith('@'):
                    if domain == pattern[1:] or domain.endswith(pattern):
                        score += 100 - (j * 10)
                        break
                elif pattern.endswith('@'):
                    pattern_prefix = pattern[:-1]
                    if username == pattern_prefix or username.startswith(pattern_prefix):
                        score += 100 - (j * 10)
                        break
            
            scores.append((email, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        print("   Ranking:")
        for rank, (email, score) in enumerate(scores[:3], 1):
            print(f"     {rank}. {email} (score: {score})")

def main():
    """Run email priority tests"""
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not running. Start it first with: python main.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API. Make sure it's running at localhost:8000")
        return
    
    print("✅ API is running\n")
    
    # Run tests
    test_priority_scoring()
    # test_email_priority()  # Uncomment to test with real API calls
    
    print("\n✅ Email priority testing completed!")
    print("\nTo test with real domains, uncomment the test_email_priority() call")
    print("and make sure you have domains that actually contain emails.")

if __name__ == "__main__":
    main()