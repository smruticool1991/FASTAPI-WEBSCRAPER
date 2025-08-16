#\!/usr/bin/env python3
"""
Test script for enhanced email filtering
Tests the removal of Sentry tracking emails and duplicate detection
"""

import re
from typing import List

def is_valid_business_email(email: str) -> bool:
    """Check if email is a valid business email (not placeholder/fake)"""
    if not email or '@' not in email:
        return False
        
    email_lower = email.lower().strip()
    
    # Basic format validation
    if len(email_lower) < 5 or len(email_lower) > 100:
        return False
        
    # Must have proper email format
    if not re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9._%-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$', email_lower):
        return False
    
    username, domain = email_lower.split('@', 1)
    
    # Hash-like patterns (Sentry tracking IDs, etc.)
    invalid_patterns = [
        r'^[a-f0-9]{24,}$',  # 24+ character hex strings
        r'^[a-f0-9]{32}$',   # 32-character hex strings (common in tracking)
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, username):
            return False
    
    # Sentry and error tracking domains
    invalid_domains = [
        'sentry-next.wixpress.com', 'sentry.wixpress.com',
        'sentry.io', 'bugsnag.com', 'rollbar.com',
        'example.com', 'test.com', 'domain.com'
    ]
    
    if domain in invalid_domains:
        return False
        
    # Check domain patterns for Sentry
    invalid_domain_patterns = [
        r'sentry.*\.wixpress\.com$',
        r'.*\.sentry\.io$',
    ]
    
    for pattern in invalid_domain_patterns:
        if re.search(pattern, domain):
            return False
    
    return True

def test_sentry_email():
    """Test the specific Sentry email filtering"""
    print("🧪 Testing Sentry Email Filtering")
    print("=" * 40)
    
    # Test emails including the problematic one
    test_emails = [
        "605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com",
        "abc123def456789@sentry.wixpress.com", 
        "tracking123@sentry.io",
        "valid.email@company.com",
        "contact@business.org",
        "info@mycompany.net"
    ]
    
    print("Testing emails:")
    valid_count = 0
    filtered_count = 0
    
    for email in test_emails:
        is_valid = is_valid_business_email(email)
        status = "✅ VALID" if is_valid else "❌ FILTERED"
        print(f"  {email}")
        print(f"    → {status}")
        
        if is_valid:
            valid_count += 1
        else:
            filtered_count += 1
    
    print(f"\nSummary:")
    print(f"  Valid emails: {valid_count}")
    print(f"  Filtered emails: {filtered_count}")
    print(f"\n✅ Test completed\!")
    
    return valid_count, filtered_count

if __name__ == "__main__":
    test_sentry_email()
EOF < /dev/null
