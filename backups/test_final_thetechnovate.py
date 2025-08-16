#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

async def test_thetechnovate_final():
    """Final test with thetechnovate.com homepage using enhanced email protection"""
    
    analyzer = WebsiteAnalyzer()
    
    print("=== FINAL TEST: thetechnovate.com ===")
    print("Testing enhanced email extraction with CloudFlare protection support")
    print()
    
    # Test the homepage
    print("Analyzing homepage...")
    result = await analyzer.analyze_website("thetechnovate.com", timeout=30)
    
    print(f"Domain: {result.domain}")
    print(f"Status: {result.status}")
    print(f"Platform: {result.platform}")
    print()
    
    print("=== EMAIL EXTRACTION RESULTS ===")
    print(f"Emails found: {result.emails}")
    print(f"Email count: {result.emailCount}")
    
    if result.emails:
        print("SUCCESS! Found protected emails:")
        for i, email in enumerate(result.emails, 1):
            print(f"  {i}. {email}")
    else:
        print("No emails found")
    
    print()
    print("=== OTHER CONTACT INFO ===")
    print(f"Phones: {result.phones}")
    print(f"Contact pages: {len(result.contactPages)} found")
    if result.contactPages:
        for page in result.contactPages[:2]:
            print(f"  - {page['linkText']}: {page['url']}")
    
    print()
    print("=== SOCIAL MEDIA ===")
    print(f"Total social links: {result.totalSocialLinks}")
    for platform, has_links in [
        ('Facebook', result.hasFacebook),
        ('Twitter', result.hasTwitter), 
        ('LinkedIn', result.hasLinkedin),
        ('Instagram', result.hasInstagram),
        ('YouTube', result.hasYoutube)
    ]:
        if has_links == 'Yes':
            print(f"  + {platform}")
    
    print()
    print("=== SEO ANALYSIS ===")
    print(f"SEO Score: {result.seoScore}/100 (Grade: {result.seoGrade})")
    print(f"Title: {result.hasTitle} (Length: {result.titleLength})")
    print(f"Meta Description: {result.hasDescription} (Length: {result.descriptionLength})")
    
    if result.error:
        print(f"\nError: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_thetechnovate_final())