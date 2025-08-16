#!/usr/bin/env python3
import asyncio
import aiohttp
import re
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

async def examine_contact_page():
    """Examine the contact page content in detail"""
    analyzer = WebsiteAnalyzer()
    
    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=10,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        url = "https://thetechnovate.com/contact/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            content = await response.text(errors='ignore')
            
            print(f"Contact page analysis for {url}")
            print(f"Content length: {len(content)}")
            
            # Search for various email patterns
            email_searches = [
                'info@thetechnovate.com',
                'info@',
                '@thetechnovate.com',
                '@thetechnovate',
                'info&#64;',
                '&#64;thetechnovate',
                'info[at]',
                '[at]thetechnovate',
                'info',
                'thetechnovate',
                'email',
                'contact',
                'mailto:',
            ]
            
            print(f"\nSearching for email patterns:")
            for pattern in email_searches:
                if pattern.lower() in content.lower():
                    count = content.lower().count(pattern.lower())
                    print(f"  '{pattern}': Found {count} times")
                    
                    # Show context for first few matches
                    if count > 0 and count <= 3:
                        positions = []
                        start = 0
                        while True:
                            pos = content.lower().find(pattern.lower(), start)
                            if pos == -1:
                                break
                            positions.append(pos)
                            start = pos + 1
                            if len(positions) >= 3:
                                break
                        
                        for i, pos in enumerate(positions):
                            context_start = max(0, pos - 50)
                            context_end = min(len(content), pos + 50)
                            context = content[context_start:context_end].replace('\n', '\\n')
                            print(f"    Context {i+1}: ...{context}...")
                else:
                    print(f"  '{pattern}': Not found")
            
            # Look for JavaScript that might contain emails
            print(f"\nLooking for JavaScript patterns:")
            js_patterns = [
                r'var\s+[^=]*email[^=]*=\s*["\']([^"\']*)["\']',
                r'email\s*:\s*["\']([^"\']*)["\']',
                r'contact[^=]*=\s*["\']([^"\']*@[^"\']*)["\']',
                r'"([^"]*@[^"]*)"',
                r"'([^']*@[^']*)'",
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"  Pattern '{pattern}': {matches[:5]}")  # Show first 5 matches
            
            # Look for data attributes
            print(f"\nLooking for data attributes:")
            data_patterns = [
                r'data-email=["\']([^"\']*)["\']',
                r'data-contact=["\']([^"\']*)["\']',
                r'href=["\']mailto:([^"\']*)["\']',
            ]
            
            for pattern in data_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"  Pattern '{pattern}': {matches}")
            
            # Show a larger sample of the contact section
            print(f"\nLooking for contact sections:")
            contact_section_patterns = [
                r'contact[^>]*>([^<]{0,500})',
                r'email[^>]*>([^<]{0,200})',
                r'get in touch[^>]*>([^<]{0,300})',
            ]
            
            for pattern in contact_section_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                if matches:
                    print(f"  Contact section found:")
                    for match in matches[:2]:  # Show first 2
                        clean_match = match.replace('\n', ' ').strip()[:200]
                        print(f"    {clean_match}...")
            
            # Test our enhanced email extraction manually
            print(f"\nTesting manual email extraction:")
            emails = analyzer.extract_emails(content)
            print(f"  Extracted emails: {emails}")
            
            # Save a snippet of the content to file for manual inspection
            print(f"\nSaving content snippet to contact_snippet.html...")
            # Find sections that might contain contact info
            snippet_keywords = ['contact', 'email', 'touch', 'reach', 'info']
            snippet_content = ""
            
            for keyword in snippet_keywords:
                keyword_pos = content.lower().find(keyword)
                if keyword_pos != -1:
                    start = max(0, keyword_pos - 500)
                    end = min(len(content), keyword_pos + 1500)
                    snippet_content += f"\n\n=== Section containing '{keyword}' ===\n"
                    snippet_content += content[start:end]
            
            with open('contact_snippet.html', 'w', encoding='utf-8', errors='ignore') as f:
                f.write(snippet_content)
            
            print("Done! Check contact_snippet.html for manual inspection.")

if __name__ == "__main__":
    asyncio.run(examine_contact_page())