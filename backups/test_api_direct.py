#!/usr/bin/env python3
import asyncio
import aiohttp
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

async def test_technovate_direct():
    """Test email extraction directly with thetechnovate.com"""
    analyzer = WebsiteAnalyzer()
    
    print("Testing thetechnovate.com email extraction...")
    
    try:
        # Test the analyzer directly
        result = await analyzer.analyze_website("thetechnovate.com", timeout=30)
        
        print(f"Domain: {result.domain}")
        print(f"Status: {result.status}")
        print(f"Platform: {result.platform}")
        print(f"Emails found: {result.emails}")
        print(f"Email count: {result.emailCount}")
        
        if result.error:
            print(f"Error: {result.error}")
            
        # If no emails found, let's debug the HTML content
        if not result.emails:
            print("\nNo emails found. Let's check the raw content...")
            
            # Fetch raw content for debugging
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            async with aiohttp.ClientSession(connector=connector) as session:
                fetch_result = await analyzer.fetch_website(session, "thetechnovate.com", 30)
                
                if 'content' in fetch_result:
                    html = fetch_result['content']
                    print(f"HTML content length: {len(html)}")
                    
                    # Check if email appears in raw HTML
                    if 'info@thetechnovate.com' in html.lower():
                        print("+ Email found in raw HTML!")
                    else:
                        print("- Email NOT found in raw HTML")
                    
                    # Check for obfuscated versions
                    if 'info&#64;thetechnovate' in html.lower():
                        print("+ HTML entity obfuscated email found!")
                    elif 'info[at]thetechnovate' in html.lower():
                        print("+ [at] obfuscated email found!")
                    elif 'info@' in html.lower():
                        print("+ Partial email pattern found!")
                    else:
                        print("- No obvious email patterns found")
                    
                    # Show a sample of the HTML content
                    print(f"\nHTML sample (first 1000 chars):")
                    print(html[:1000])
                    
                    # Look for contact page
                    if '/contact' in html.lower() or 'contact' in html.lower():
                        print("\n+ Contact page references found")
                        
                        # Try to fetch the contact page
                        print("Trying to fetch contact page...")
                        contact_result = await analyzer.fetch_website(session, "thetechnovate.com/contact", 30)
                        
                        if 'content' in contact_result:
                            contact_html = contact_result['content']
                            print(f"Contact page HTML length: {len(contact_html)}")
                            
                            # Test email extraction on contact page
                            contact_emails = analyzer.extract_emails(contact_html)
                            print(f"Emails found on contact page: {contact_emails}")
                            
                            if 'info@thetechnovate.com' in contact_html.lower():
                                print("+ Email found in contact page!")
                            
                            # Show contact page sample
                            print(f"\nContact page sample (first 1000 chars):")
                            print(contact_html[:1000])
                        else:
                            print("Failed to fetch contact page")
                else:
                    print("Failed to fetch HTML content")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_technovate_direct())