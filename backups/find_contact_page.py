#!/usr/bin/env python3
import asyncio
import aiohttp
import re
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

async def find_contact_page():
    """Find the correct contact page URL for thetechnovate.com"""
    analyzer = WebsiteAnalyzer()
    
    # Common contact page URL patterns
    contact_urls = [
        "https://thetechnovate.com/contact",
        "https://thetechnovate.com/contact-us",
        "https://thetechnovate.com/contact/",
        "https://thetechnovate.com/contact-us/",
        "https://thetechnovate.com/get-in-touch",
        "https://thetechnovate.com/reach-out",
        "https://thetechnovate.com/about/contact",
        "https://thetechnovate.com/pages/contact",
    ]
    
    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=10,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # First, get the main page HTML and look for contact page links
        print("Fetching main page to find contact page links...")
        main_result = await analyzer.fetch_website(session, "thetechnovate.com", 30)
        
        if 'content' in main_result:
            html = main_result['content']
            
            # Look for contact page links in the HTML
            contact_patterns = [
                r'href=["\']([^"\']*contact[^"\']*)["\'"]',
                r'href=["\']([^"\']*get-in-touch[^"\']*)["\'"]',
                r'href=["\']([^"\']*reach[^"\']*)["\'"]',
            ]
            
            found_links = []
            for pattern in contact_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                found_links.extend(matches)
            
            print(f"Found potential contact links: {found_links[:10]}")
            
            # Try each found link
            for link in found_links[:5]:  # Try first 5
                if link.startswith('/'):
                    full_url = f"https://thetechnovate.com{link}"
                elif link.startswith('http'):
                    full_url = link
                else:
                    full_url = f"https://thetechnovate.com/{link}"
                
                print(f"\nTrying: {full_url}")
                
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                    }
                    
                    async with session.get(full_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            content = await response.text(errors='ignore')
                            print(f"  Status: {response.status} - Content length: {len(content)}")
                            
                            # Test email extraction on this page
                            emails = analyzer.extract_emails(content)
                            print(f"  Emails found: {emails}")
                            
                            if emails:
                                print(f"  SUCCESS! Found emails on {full_url}")
                                
                                # Show some content around the email
                                if 'info@thetechnovate.com' in content.lower():
                                    email_pos = content.lower().find('info@thetechnovate.com')
                                    start = max(0, email_pos - 100)
                                    end = min(len(content), email_pos + 100)
                                    print(f"  Context: ...{content[start:end]}...")
                                
                                return full_url, emails
                        else:
                            print(f"  Status: {response.status}")
                            
                except Exception as e:
                    print(f"  Error: {e}")
        
        # If no links found in main page, try common patterns
        print(f"\nTrying common contact page URLs...")
        for url in contact_urls:
            print(f"Trying: {url}")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.text(errors='ignore')
                        print(f"  Status: {response.status} - Content length: {len(content)}")
                        
                        emails = analyzer.extract_emails(content)
                        print(f"  Emails found: {emails}")
                        
                        if emails:
                            print(f"  SUCCESS! Found emails on {url}")
                            return url, emails
                    else:
                        print(f"  Status: {response.status}")
                        
            except Exception as e:
                print(f"  Error: {e}")
    
    print("No contact page with emails found")
    return None, []

if __name__ == "__main__":
    asyncio.run(find_contact_page())