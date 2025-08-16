#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

async def test_ssl_fallback():
    """Test SSL fallback handling with problematic domains"""
    
    analyzer = WebsiteAnalyzer()
    
    # Test domains with various SSL issues
    test_domains = [
        "httpbin.org",  # Known working domain (should work)
        "self-signed.badssl.com",  # Self-signed certificate
        "expired.badssl.com",  # Expired certificate  
        "wrong.host.badssl.com",  # Wrong hostname
        "thick-aluminum-plate.com",  # The original problem domain
    ]
    
    print("=== SSL/TLS Fallback Testing ===")
    print("Testing websites with various SSL certificate issues")
    print()
    
    for domain in test_domains:
        print(f"Testing: {domain}")
        print("-" * 50)
        
        try:
            result = await analyzer.analyze_website(domain, timeout=20)
            
            print(f"Status: {result.status}")
            print(f"Platform: {result.platform}")
            print(f"HTTPS: {result.isHttps}")
            
            if result.emails:
                print(f"Emails: {result.emails}")
            else:
                print("Emails: None found")
                
            if result.error:
                print(f"Error: {result.error}")
            else:
                print("Success: Website analyzed successfully")
                
        except Exception as e:
            print(f"Exception: {e}")
            
        print()
    
    print("=== Summary ===")
    print("The enhanced HTTP client should now handle:")
    print("+ Self-signed certificates")
    print("+ Expired certificates") 
    print("+ Certificate hostname mismatches")
    print("+ SSL/TLS connection failures")
    print("+ Automatic HTTPS -> HTTP fallback")
    print("+ Proper error reporting for unreachable sites")

if __name__ == "__main__":
    asyncio.run(test_ssl_fallback())