import asyncio
import aiohttp
from main import WebsiteAnalyzer

async def test_email_extraction_real():
    """Test email extraction with a real website"""
    analyzer = WebsiteAnalyzer()
    
    # Test with a simple HTML sample that mimics real website content
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contact Us - Business Company</title>
        <meta name="description" content="Contact Business Company for all your needs">
    </head>
    <body>
        <header>
            <nav>
                <a href="/home">Home</a>
                <a href="/services">Services</a>
                <a href="/contact">Contact</a>
            </nav>
        </header>
        
        <main>
            <h1>Contact Our Team</h1>
            <p>Get in touch with us today!</p>
            
            <div class="contact-info">
                <p>General inquiries: <a href="mailto:info@businesscompany.com">info@businesscompany.com</a></p>
                <p>Sales team: <a href="mailto:sales@businesscompany.com">sales@businesscompany.com</a></p>
                <p>Support: support@businesscompany.com</p>
                <p>CEO: john.smith@businesscompany.com</p>
                <p>Customer service: help@businesscompany.com</p>
            </div>
            
            <div class="office-info">
                <p>Phone: +1 (555) 123-4567</p>
                <p>Address: 123 Business St, City, State 12345</p>
            </div>
            
            <div class="social-links">
                <a href="https://facebook.com/businesscompany">Facebook</a>
                <a href="https://twitter.com/businesscompany">Twitter</a>
                <a href="https://linkedin.com/company/businesscompany">LinkedIn</a>
            </div>
        </main>
        
        <footer>
            <p>&copy; 2024 Business Company. All rights reserved.</p>
            <p>Privacy: privacy@businesscompany.com</p>
            <!-- Some tracking stuff that should be filtered -->
            <script>
                window.dataLayer = window.dataLayer || [];
                var trackingEmail = "tracking@analytics.com";
            </script>
        </footer>
    </body>
    </html>
    """
    
    print("Testing email extraction with improved algorithm...")
    emails = analyzer.extract_emails(test_html)
    print(f"Extracted emails: {emails}")
    print(f"Number of emails found: {len(emails)}")
    
    # Test phone extraction too
    phones = analyzer.extract_phones(test_html)
    print(f"Extracted phones: {phones}")
    
    # Test contact page extraction
    contact_pages = analyzer.extract_contact_pages(test_html, "https://businesscompany.com")
    print(f"Contact pages: {contact_pages}")
    
    # Test social media extraction
    social_links = analyzer.extract_social_links(test_html)
    print(f"Social links: {social_links}")

if __name__ == "__main__":
    asyncio.run(test_email_extraction_real())