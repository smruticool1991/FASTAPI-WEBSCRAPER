#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

async def test_contact_fallback():
    """Test contact page fallback for jackiemariejewelry.com"""
    
    analyzer = WebsiteAnalyzer()
    
    print("=== CONTACT PAGE FALLBACK TEST ===")
    print("Testing jackiemariejewelry.com - homepage vs contact page emails")
    print()
    
    # Test the complete analysis with fallback
    print("1. Running complete analysis with contact page fallback...")
    result = await analyzer.analyze_website("jackiemariejewelry.com", timeout=30)
    
    print(f"Domain: {result.domain}")
    print(f"Status: {result.status}")
    print(f"Platform: {result.platform}")
    print(f"HTTPS: {result.isHttps}")
    print()
    
    print("=== EMAIL RESULTS ===")
    print(f"Emails found: {result.emails}")
    print(f"Email count: {result.emailCount}")
    
    if result.emails:
        print("SUCCESS! Found emails:")
        for i, email in enumerate(result.emails, 1):
            print(f"  {i}. {email}")
    else:
        print("No emails found (check if site is accessible)")
    
    print()
    print("=== OTHER CONTACT INFO ===")
    print(f"Phones: {result.phones}")
    print(f"Phone count: {result.phoneCount}")
    
    print(f"Contact pages: {result.contactPageCount} found")
    if result.contactPages:
        for page in result.contactPages:
            print(f"  - {page['linkText']}: {page['url']}")
    
    print()
    print("=== MANUAL TESTING ===")
    print("Let's manually test homepage vs contact page...")
    
    # Test homepage only
    import aiohttp
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("\n2. Testing homepage only...")
        homepage_result = await analyzer.fetch_website(session, "jackiemariejewelry.com", 30)
        
        if 'content' in homepage_result:
            homepage_emails = analyzer.extract_emails(homepage_result['content'])
            print(f"Homepage emails: {homepage_emails}")
            print(f"Homepage email count: {len(homepage_emails)}")
            
            # Test contact page specifically
            print("\n3. Testing contact page specifically...")
            contact_emails = await analyzer.fetch_contact_page_emails(session, "jackiemariejewelry.com", 30)
            print(f"Contact page emails: {contact_emails}")
            print(f"Contact page email count: {len(contact_emails)}")
            
        else:
            print(f"Failed to fetch homepage: {homepage_result.get('error')}")
    
    if result.error:
        print(f"\nError: {result.error}")
    
    print(f"\n{'='*50}")
    print("SUMMARY:")
    print("The enhanced API now:")
    print("1. Tries to find emails on homepage first")
    print("2. If no emails found, automatically checks contact page") 
    print("3. Tries multiple contact page URL patterns")
    print("4. Returns emails from whichever page has them")
    print("5. Handles both HTTP and HTTPS contact pages")

async def test_multiple_domains():
    """Test contact fallback with multiple domains"""
    
    analyzer = WebsiteAnalyzer()
    
    test_domains = [
        "jackiemariejewelry.com",
        "thetechnovate.com",  # Known to have emails on homepage
        "httpbin.org",        # Should have emails somewhere
    ]
    
    print(f"\n{'='*60}")
    print("=== TESTING MULTIPLE DOMAINS ===")
    
    for domain in test_domains:
        print(f"\nTesting: {domain}")
        print("-" * 40)
        
        result = await analyzer.analyze_website(domain, timeout=20)
        print(f"Status: {result.status}")
        print(f"Emails: {result.emails}")
        print(f"Count: {result.emailCount}")
        
        if result.error:
            print(f"Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_contact_fallback())
    print("\n" + "="*60)
    asyncio.run(test_multiple_domains())