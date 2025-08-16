#!/usr/bin/env python3
import re
from typing import List

def extract_emails_enhanced(html: str) -> List[str]:
    """Enhanced email extraction with obfuscation handling"""
    # First, handle common obfuscation methods
    processed_html = html
    
    # Decode HTML entities
    processed_html = processed_html.replace('&#64;', '@').replace('&#46;', '.')
    processed_html = processed_html.replace('&at;', '@').replace('&dot;', '.')
    
    # Handle [at] and [dot] obfuscation
    processed_html = re.sub(r'\[at\]', '@', processed_html, flags=re.IGNORECASE)
    processed_html = re.sub(r'\[dot\]', '.', processed_html, flags=re.IGNORECASE)
    processed_html = re.sub(r'\(at\)', '@', processed_html, flags=re.IGNORECASE)
    processed_html = re.sub(r'\(dot\)', '.', processed_html, flags=re.IGNORECASE)
    
    # Handle spaced emails (up to 2 spaces around @ and .)
    processed_html = re.sub(r'(\w+)\s{1,2}@\s{1,2}(\w+(?:\.\w+)*)', r'\1@\2', processed_html)
    processed_html = re.sub(r'(\w+@\w+)\s{1,2}\.\s{1,2}(\w+)', r'\1.\2', processed_html)
    
    # Remove HTML tags that might split emails
    tag_split_pattern = r'([a-zA-Z0-9._%-]+)</[^>]+>@<[^>]+>([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    processed_html = re.sub(tag_split_pattern, r'\1@\2', processed_html)
    
    print("=== Enhanced Email Extraction Test ===")
    print(f"Original HTML length: {len(html)}")
    print(f"Processed HTML length: {len(processed_html)}")
    
    # More comprehensive email regex
    email_regex = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9._%-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b'
    email_matches = re.findall(email_regex, processed_html, re.IGNORECASE)
    
    print(f"Email matches found: {len(email_matches)}")
    for email in email_matches:
        print(f"  - {email}")
    
    return email_matches

# Test cases including the specific obfuscation methods
test_cases = [
    # Case 1: Direct email
    "Contact us at info@thetechnovate.com for more information.",
    
    # Case 2: HTML entity obfuscation
    "Email: info&#64;thetechnovate&#46;com",
    
    # Case 3: [at] [dot] obfuscation
    "Send email to info[at]thetechnovate[dot]com",
    
    # Case 4: Spaced obfuscation
    "Contact: info @ thetechnovate . com",
    
    # Case 5: HTML tag splitting
    "<span>info</span>@<span>thetechnovate.com</span>",
    
    # Case 6: Real-world complex HTML
    '''
    <div class="contact-section">
        <h3>Get in Touch</h3>
        <p>Email us at <strong>info</strong>&#64;<strong>thetechnovate</strong>&#46;<strong>com</strong></p>
        <p>Or call us at +1-904-342-3861</p>
    </div>
    ''',
    
    # Case 7: JavaScript style (common in modern websites)
    'var contactEmail = "info" + "@" + "thetechnovate.com";',
    
    # Case 8: Multiple obfuscation methods together
    "Primary: info[at]thetechnovate[dot]com | Secondary: support&#64;thetechnovate&#46;com"
]

if __name__ == "__main__":
    print("Testing enhanced email extraction...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"TEST CASE {i}:")
        print(f"Input: {test_case[:100]}...")
        emails = extract_emails_enhanced(test_case)
        print(f"Result: {emails}")
        
    print(f"\n{'='*50}")
    print("Summary: Enhanced email extraction can handle:")
    print("✓ Direct emails")
    print("✓ HTML entity obfuscation (&#64;, &#46;)")
    print("✓ [at]/[dot] obfuscation")
    print("✓ Spaced obfuscation")
    print("✓ HTML tag splitting")