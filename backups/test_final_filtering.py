#!/usr/bin/env python3
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

def test_final_filtering():
    """Final comprehensive test of email filtering"""
    
    analyzer = WebsiteAnalyzer()
    
    print("=== FINAL EMAIL FILTERING TEST ===")
    
    # All your specific problematic patterns
    test_html = '''
    <div>
        Contact us at:
        - info@realcompany.com (VALID)
        - image.png@fake.com (INVALID - file extension)
        - photo.jpg@site.com (INVALID - file extension) 
        - example@mysite.com (INVALID - placeholder)
        - demo@company.com (INVALID - placeholder)
        - user@domain.com (INVALID - generic)
        - email@domain.com (INVALID - generic)
        - "email@email.com" (INVALID - quotes + generic)
        - domain@site.com (INVALID - domain pattern)
        - website@email.com (INVALID - generic)
        - file.webp@test.org (INVALID - file extension)
        - u003eJbeeson@willowtreetutoring.com (SHOULD CLEAN)
        - support@legitbusiness.org (VALID)
        - 12345@numbers.com (INVALID - numbers only)
        - contact@real-company.co.uk (VALID)
        - noreply@system.com (INVALID - noreply)
        - admin@localhost (INVALID - system)
    </div>
    '''
    
    print("Input HTML with mixed valid/invalid emails...")
    emails = analyzer.extract_emails(test_html)
    
    print(f"\nFINAL RESULT: {emails}")
    print(f"COUNT: {len(emails)} emails found")
    
    print(f"\nExpected valid emails:")
    print("- info@realcompany.com")
    print("- Jbeeson@willowtreetutoring.com (cleaned)")
    print("- support@legitbusiness.org")
    print("- contact@real-company.co.uk")
    
    print(f"\nExpected filtered out (invalid):")
    print("- All file extensions (.png, .jpg, .webp)")
    print("- All placeholders (example@, demo@, user@domain)")
    print("- All generic patterns (email@domain, domain@site)")
    print("- All system emails (noreply@, admin@)")
    print("- All number-only usernames")
    
    # Test individual cases
    individual_tests = [
        "u003eJbeeson@willowtreetutoring.com u003e",
        "image.png@company.com", 
        "example@mysite.com",
        "user@domain.com",
        '"email@email.com"',
        "info@legitimate-business.com"
    ]
    
    print(f"\n{'='*50}")
    print("INDIVIDUAL CLEANING TESTS:")
    for test_email in individual_tests:
        cleaned = analyzer.clean_email(test_email)
        valid = analyzer.is_valid_business_email(cleaned) if cleaned else False
        extraction = analyzer.extract_emails(test_email)
        
        print(f"'{test_email}'")
        print(f"  -> Cleaned: '{cleaned}'")
        print(f"  -> Valid: {valid}")
        print(f"  -> Extracted: {extraction}")
        print()

if __name__ == "__main__":
    test_final_filtering()