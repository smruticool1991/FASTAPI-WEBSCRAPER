#!/usr/bin/env python3
import re
from typing import List

def test_email_extraction_technovate():
    """Test email extraction with the actual email from thetechnovate.com"""
    
    # Test cases that might represent how the email appears on the site
    test_cases = [
        # Direct email
        "Contact us at info@thetechnovate.com",
        
        # Email in form
        '<input type="email" placeholder="info@thetechnovate.com">',
        
        # Email with obfuscation
        "info[at]thetechnovate[dot]com",
        
        # Email in JavaScript
        'var email = "info@thetechnovate.com";',
        
        # Email with HTML entities
        "info&#64;thetechnovate&#46;com",
        
        # Email split across elements
        '<span>info</span>@<span>thetechnovate.com</span>',
        
        # Email with spaces (sometimes used to avoid scrapers)
        "info @ thetechnovate . com",
        
        # Email in data attributes
        'data-email="info@thetechnovate.com"',
        
        # Complete HTML sample similar to contact page
        '''
        <div class="contact-info">
            <p>Email: info@thetechnovate.com</p>
            <p>Phone: +1-904-342-3861</p>
        </div>
        '''
    ]
    
    # Current regex from main.py
    email_regex = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9._%-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b'
    
    print("Testing email extraction with various formats...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {test_case[:50]}...")
        matches = re.findall(email_regex, test_case, re.IGNORECASE)
        print(f"  Matches found: {matches}")
        
        # Also test with a more comprehensive regex
        comprehensive_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        comp_matches = re.findall(comprehensive_regex, test_case, re.IGNORECASE)
        print(f"  Comprehensive matches: {comp_matches}")
        
        # Test for obfuscated emails
        obfuscated = re.findall(r'[a-zA-Z0-9._%+-]+\[at\][a-zA-Z0-9.-]+\[dot\][a-zA-Z]{2,}', test_case, re.IGNORECASE)
        if obfuscated:
            print(f"  Obfuscated emails: {obfuscated}")
            
        # Test for HTML entities
        entity_test = test_case.replace('&#64;', '@').replace('&#46;', '.')
        if entity_test != test_case:
            entity_matches = re.findall(email_regex, entity_test, re.IGNORECASE)
            print(f"  After HTML entity decode: {entity_matches}")

if __name__ == "__main__":
    test_email_extraction_technovate()