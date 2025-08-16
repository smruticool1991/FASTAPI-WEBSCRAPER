#!/usr/bin/env python3
import asyncio
import aiohttp
import re
import sys
sys.path.append('.')

async def check_homepage_protection():
    """Check what email protection is used on thetechnovate.com homepage"""
    
    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=10,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        url = "https://thetechnovate.com/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            content = await response.text(errors='ignore')
            
            print(f"Homepage analysis for {url}")
            print(f"Content length: {len(content)}")
            
            # Look for various email protection patterns
            protection_patterns = {
                'CloudFlare Email Protection': r'<a href="/cdn-cgi/l/email-protection"[^>]*>([^<]*)</a>',
                'CloudFlare data-cfemail': r'data-cfemail="([a-f0-9]+)"',
                'Encrypted email spans': r'<span[^>]*class="[^"]*email[^"]*"[^>]*>([^<]*)</span>',
                'Base64 encoded emails': r'[a-zA-Z0-9+/]{20,}={0,2}',
                'ROT13 encoded': r'vasb@',  # info@ in ROT13
                'Hexadecimal encoded': r'&#x[0-9a-fA-F]+;',
                'JavaScript email decode': r'function\s+[^(]*email[^(]*\([^)]*\)',
                'Email protection services': r'(mailhide|cryptemail|antispam)',
            }
            
            print(f"\nLooking for email protection patterns:")
            
            for pattern_name, pattern in protection_patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"+ {pattern_name}: Found {len(matches)} matches")
                    if len(matches) <= 5:  # Show first 5 matches
                        for match in matches:
                            print(f"    {match}")
                else:
                    print(f"- {pattern_name}: Not found")
            
            # Look for specific email-related strings that might be protected
            email_search_terms = [
                'info@',
                '@thetechnovate',
                'email',
                'contact',
                'cfemail',
                '/cdn-cgi/l/email-protection',
                'data-cfemail',
                '__cf_email__',
            ]
            
            print(f"\nSearching for email-related content:")
            for term in email_search_terms:
                if term.lower() in content.lower():
                    count = content.lower().count(term.lower())
                    print(f"+ '{term}': Found {count} times")
                    
                    # Show context for CloudFlare protection specifically
                    if 'cfemail' in term or 'email-protection' in term:
                        positions = []
                        start = 0
                        while True:
                            pos = content.lower().find(term.lower(), start)
                            if pos == -1:
                                break
                            positions.append(pos)
                            start = pos + 1
                            if len(positions) >= 3:
                                break
                        
                        for i, pos in enumerate(positions):
                            context_start = max(0, pos - 100)
                            context_end = min(len(content), pos + 200)
                            context = content[context_start:context_end].replace('\n', '\\n')
                            print(f"    Context {i+1}: ...{context}...")
                else:
                    print(f"- '{term}': Not found")
            
            # Save snippet for manual inspection
            if 'cfemail' in content or 'email-protection' in content:
                print(f"\nSaving homepage snippet for CloudFlare email protection analysis...")
                with open('homepage_snippet.html', 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(content)
                print("Saved to homepage_snippet.html")

if __name__ == "__main__":
    asyncio.run(check_homepage_protection())