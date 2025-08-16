#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

async def test_contact_examples():
    """Test contact page fallback with domains likely to have contact page emails"""
    
    analyzer = WebsiteAnalyzer()
    
    print("=== CONTACT PAGE FALLBACK EXAMPLES ===")
    print()
    
    # Test domains that might have emails on contact pages but not homepage
    test_domains = [
        "jackiemariejewelry.com",  # Original request
        "small-business-example.com",  # Might not exist
        "httpbin.org",  # Known working site
    ]
    
    for domain in test_domains:
        print(f"Testing: {domain}")
        print("-" * 50)
        
        try:
            result = await analyzer.analyze_website(domain, timeout=30)
            
            print(f"Status: {result.status}")
            print(f"Platform: {result.platform}")
            
            # Show the progression
            print(f"\nEmail Results:")
            if result.emails:
                print(f"✓ Found {len(result.emails)} emails:")
                for email in result.emails:
                    print(f"  - {email}")
            else:
                print("✗ No emails found on homepage or contact pages")
            
            # Show contact pages found
            if result.contactPages:
                print(f"\nContact pages detected:")
                for page in result.contactPages:
                    print(f"  - {page['linkText']}: {page['url']}")
            
            # Show other contact info
            if result.phones:
                print(f"\nPhones found: {result.phones}")
            
            print()
            
        except Exception as e:
            print(f"Error testing {domain}: {e}")
            print()
    
    print("="*60)
    print("MANUAL VERIFICATION - Let's check jackiemariejewelry.com contact page")
    
    # Manual verification of the specific contact page
    import aiohttp
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        
        # Test the specific Shopify contact page pattern
        shopify_contact = "https://jackiemariejewelry.com/pages/contact"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            async with session.get(shopify_contact, headers=headers, ssl=False) as response:
                if response.status == 200:
                    content = await response.text(errors='ignore')
                    print(f"\n✓ Successfully loaded: {shopify_contact}")
                    print(f"Content length: {len(content)} characters")
                    
                    # Look for any email patterns in the content
                    import re
                    all_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                    print(f"Raw email matches: {all_emails}")
                    
                    # Test our extraction
                    extracted = analyzer.extract_emails(content)
                    print(f"Extracted valid emails: {extracted}")
                    
                    # Check for contact form or hidden contact info
                    if 'contact' in content.lower():
                        print("✓ Contact-related content found")
                    if 'email' in content.lower():
                        print("✓ Email-related content found") 
                    if 'form' in content.lower():
                        print("✓ Form elements found (may use contact forms instead of visible emails)")
                    
                    # Show a sample of the content
                    print(f"\nContent sample (first 500 chars):")
                    print(content[:500])
                    
                else:
                    print(f"✗ Failed to load contact page: HTTP {response.status}")
                    
        except Exception as e:
            print(f"✗ Error loading contact page: {e}")

if __name__ == "__main__":
    asyncio.run(test_contact_examples())