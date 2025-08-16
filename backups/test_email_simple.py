#!/usr/bin/env python3

import re
from typing import List

def extract_emails_simple(html: str) -> List[str]:
    """Simple email extraction for testing"""
    # More comprehensive email regex
    email_regex = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9._%-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b'
    email_matches = re.findall(email_regex, html, re.IGNORECASE)
    
    print(f"Found {len(email_matches)} potential emails:")
    for email in email_matches:
        print(f"  - {email}")
    
    # Simple filtering
    valid_emails = []
    blacklist = ['noreply', 'no-reply', 'example.com', 'test.com', 'tracking', 'analytics']
    
    for email in set(email_matches):  # Remove duplicates
        email_lower = email.lower()
        
        # Check length
        if len(email_lower) < 5 or len(email_lower) > 100:
            continue
            
        # Check blacklist
        if any(pattern in email_lower for pattern in blacklist):
            print(f"  FILTERED: {email} (blacklist)")
            continue
            
        valid_emails.append(email)
        print(f"  VALID: {email}")
    
    return valid_emails[:3]  # Return top 3

# Test with sample HTML
test_html = """
<html>
<head><title>Contact Us</title></head>
<body>
    <p>Contact us at info@company.com</p>
    <p>Sales: sales@company.com</p>
    <p>Support: support@company.com</p>
    <a href="mailto:hello@business.org">Email us</a>
    <div>CEO: john.doe@company.com</div>
    <span>noreply@system.com</span>
    <script>tracking@analytics.com</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("Testing simple email extraction...")
    emails = extract_emails_simple(test_html)
    print(f"\nFinal emails: {emails}")
    print(f"Count: {len(emails)}")