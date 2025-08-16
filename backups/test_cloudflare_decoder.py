#!/usr/bin/env python3
import sys
sys.path.append('.')
from main import WebsiteAnalyzer

def test_cloudflare_decoder():
    """Test CloudFlare email decoder with actual data from thetechnovate.com"""
    
    analyzer = WebsiteAnalyzer()
    
    # The actual encrypted email from thetechnovate.com homepage
    test_html = '''
    <span class="__cf_email__" data-cfemail="254c4b434a65514d405140464d4b4a534451400b464a48">[email&#160;protected]</span>
    '''
    
    print("Testing CloudFlare Email Decoder")
    print("=" * 40)
    print(f"Input HTML: {test_html.strip()}")
    print()
    
    # Test the decoder directly
    emails = analyzer.decode_cloudflare_emails(test_html)
    print(f"Decoded emails: {emails}")
    
    # Test the full email extraction pipeline
    all_emails = analyzer.extract_emails(test_html)
    print(f"Full extraction result: {all_emails}")
    
    # Manual verification of the CloudFlare algorithm
    print("\nManual CloudFlare decoding verification:")
    encrypted = "254c4b434a65514d405140464d4b4a534451400b464a48"
    print(f"Encrypted string: {encrypted}")
    
    if len(encrypted) >= 2:
        key = int(encrypted[:2], 16)  # First 2 chars as hex
        encrypted_email = encrypted[2:]
        print(f"Key: {key} (0x{key:02x})")
        print(f"Encrypted part: {encrypted_email}")
        
        decoded_chars = []
        for i in range(0, len(encrypted_email), 2):
            if i + 1 < len(encrypted_email):
                hex_pair = encrypted_email[i:i+2]
                char_code = int(hex_pair, 16) ^ key
                char = chr(char_code) if 32 <= char_code <= 126 else '?'
                decoded_chars.append(char)
                print(f"  {hex_pair} -> {char_code} ^ {key} = {char_code ^ key} = '{char}'")
        
        decoded_email = ''.join(decoded_chars)
        print(f"Final decoded email: '{decoded_email}'")
    
    # Test with other common email protection methods
    other_test_cases = [
        # HTML entities
        "Contact: info&#64;example&#46;com",
        
        # Mixed protection
        'Email us at <span class="__cf_email__" data-cfemail="7c0e1315113c08140908191f14121308190819521f1311">[email&#160;protected]</span>',
        
        # Multiple emails
        '''
        <span class="__cf_email__" data-cfemail="254c4b434a65514d405140464d4b4a534451400b464a48">[email&#160;protected]</span>
        <span class="__cf_email__" data-cfemail="7c0e1315113c08140908191f14121308190819521f1311">[email&#160;protected]</span>
        '''
    ]
    
    print("\nTesting other protection methods:")
    print("=" * 40)
    
    for i, test_case in enumerate(other_test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {test_case[:100]}...")
        emails = analyzer.extract_emails(test_case)
        print(f"Extracted: {emails}")

if __name__ == "__main__":
    test_cloudflare_decoder()