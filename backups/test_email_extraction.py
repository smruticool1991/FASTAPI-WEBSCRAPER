import re
from typing import List

class EmailExtractorDebug:
    def __init__(self):
        # Reduced blacklist for testing
        self.email_blacklist_patterns = [
            'example.com', 'test.com', 'placeholder', 'noreply', 'no-reply',
            'sentry.io', 'tracking', 'analytics', 'localhost', '.ru'
        ]
        
        self.generic_usernames = [
            'info', 'admin', 'support', 'contact', 'help', 'sales', 'service',
            'team', 'hello', 'mail', 'email', 'webmaster'
        ]

    def extract_emails_debug(self, html: str) -> List[str]:
        """Debug version of email extraction"""
        print("=== EMAIL EXTRACTION DEBUG ===")
        
        # More comprehensive email regex
        email_regex = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9._%-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b'
        email_matches = re.findall(email_regex, html, re.IGNORECASE)
        
        print(f"Raw email matches found: {len(email_matches)}")
        for i, email in enumerate(email_matches[:10]):  # Show first 10
            print(f"  {i+1}. {email}")
        
        if len(email_matches) > 10:
            print(f"  ... and {len(email_matches) - 10} more")
        
        # Remove duplicates (case insensitive)
        unique_emails = []
        seen_emails = set()
        for email in email_matches:
            email_lower = email.lower()
            if email_lower not in seen_emails:
                seen_emails.add(email_lower)
                unique_emails.append(email)
        
        print(f"\nUnique emails: {len(unique_emails)}")
        
        # Apply filters
        valid_emails = []
        for email in unique_emails:
            email_lower = email.lower().strip()
            
            # Skip if @ not in email (shouldn't happen with regex, but safety check)
            if '@' not in email_lower:
                print(f"FILTERED (no @): {email}")
                continue
                
            username, domain = email_lower.split('@', 1)
            
            # Length validation
            if len(email_lower) < 5 or len(email_lower) > 100:  # Increased max length
                print(f"FILTERED (length {len(email_lower)}): {email}")
                continue
            
            # Check against blacklisted patterns (more lenient)
            is_blacklisted = False
            for pattern in self.email_blacklist_patterns:
                if pattern in email_lower:
                    print(f"FILTERED (blacklist '{pattern}'): {email}")
                    is_blacklisted = True
                    break
            
            if is_blacklisted:
                continue
            
            # Check for hash-like emails (more lenient)
            if re.match(r'^[a-f0-9]{20,}@', email_lower):
                print(f"FILTERED (hash-like): {email}")
                continue
            
            # Filter out emails that are obviously not contact emails
            suspicious_patterns = [
                r'\.(png|jpg|jpeg|gif|svg|webp|ico|css|js|json|xml)@',
                r'^[0-9]+@',  # emails starting with only numbers
                r'[0-9]{8,}@'  # long number sequences
            ]
            
            is_suspicious = False
            for pattern in suspicious_patterns:
                if re.search(pattern, email_lower):
                    print(f"FILTERED (suspicious pattern '{pattern}'): {email}")
                    is_suspicious = True
                    break
                    
            if is_suspicious:
                continue
                
            print(f"VALID: {email}")
            valid_emails.append(email)
        
        print(f"\nFinal valid emails: {len(valid_emails)}")
        
        # Score and sort emails by quality
        scored_emails = []
        for email in valid_emails:
            score = self.score_email_debug(email)
            scored_emails.append((email, score))
            print(f"SCORED: {email} -> {score}")
        
        scored_emails.sort(key=lambda x: x[1], reverse=True)
        final_emails = [email for email, score in scored_emails[:3]]  # Return top 3
        
        print(f"\nTop emails returned: {final_emails}")
        return final_emails

    def score_email_debug(self, email: str) -> int:
        """Debug version of email scoring"""
        score = 100
        email_lower = email.lower()
        username, domain = email_lower.split('@', 1)
        
        # Penalize generic usernames (less strict)
        if username in self.generic_usernames:
            score -= 20  # Reduced penalty
            
        # Penalize numbers at end (less strict)
        if re.search(r'\d{3,}$', username):  # Only penalize 3+ digits
            score -= 10
            
        # Bonus for personal-looking emails
        if re.match(r'^[a-z]+\.[a-z]+$', username) and len(username) > 3:
            score += 30
            
        # Bonus for non-generic providers
        generic_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        if domain not in generic_providers:
            score += 25  # Increased bonus for company domains
            
        return score

# Test with sample HTML content
def test_email_extraction():
    extractor = EmailExtractorDebug()
    
    sample_html = """
    <html>
    <head><title>Contact Us</title></head>
    <body>
        <p>Contact us at info@company.com or sales@company.com</p>
        <div>Email: john.doe@example.org</div>
        <a href="mailto:support@testsite.net">Support</a>
        <span>noreply@system.com</span>
        <div>Follow us on social media</div>
        <p>Customer service: help@business.co.uk</p>
        <footer>webmaster@site.org | privacy@company.com</footer>
        <!-- Some noise -->
        <script>var email = "tracking@analytics.com";</script>
        <style>.email::before { content: "fake@example.com"; }</style>
    </body>
    </html>
    """
    
    print("Testing with sample HTML...")
    emails = extractor.extract_emails_debug(sample_html)
    print(f"\nFINAL RESULT: {emails}")

if __name__ == "__main__":
    test_email_extraction()