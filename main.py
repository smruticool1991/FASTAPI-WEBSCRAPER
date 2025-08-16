from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any, Union
import asyncio
import aiohttp
import time
from datetime import datetime
import logging
import re
from urllib.parse import urljoin, urlparse
import json
from collections import deque
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Website Analysis API",
    description="High-performance Python API for website analysis and scraping",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class AnalysisRequest(BaseModel):
    domains: List[str]
    batch_size: Optional[int] = 10
    timeout: Optional[int] = 15
    include_content: Optional[bool] = False
    email_priority: Optional[List[str]] = ["info@", "sales@", "@gmail.com"]  # Email priority order

class AnalysisJobRequest(BaseModel):
    domains: List[str]
    batch_size: Optional[int] = 20
    timeout: Optional[int] = 15
    priority: Optional[int] = 1  # 1=low, 2=normal, 3=high
    callback_url: Optional[str] = None
    email_priority: Optional[List[str]] = ["info@", "sales@", "@gmail.com"]  # Email priority order

class JobStatus(BaseModel):
    job_id: str
    status: str  # 'queued', 'processing', 'completed', 'failed'
    total_domains: int
    processed_domains: int
    results: List[Dict[str, Any]]  # Will contain AnalysisResponse data
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

class AnalysisResponse(BaseModel):
    domain: str
    platform: str
    purpose: str
    isHttps: str
    hasHSTS: str
    hasCSP: str
    hasXFrameOptions: str
    hasTitle: str
    titleLength: int
    titleOptimal: str
    hasDescription: str
    descriptionLength: int
    descriptionOptimal: str
    hasH1: str
    h1Count: int
    hasH2: str
    hasViewport: str
    hasCanonical: str
    hasRobots: str
    hasStructuredData: str
    hasOpenGraph: str
    hasTwitterCard: str
    hasLazyLoading: str
    hasPreload: str
    hasAltTags: str
    hasLang: str
    emails: List[str]
    emailCount: int
    phones: List[str]
    phoneCount: int
    contactPages: List[Dict[str, str]]
    contactPageCount: int
    hasContactPage: str
    socialLinks: Dict[str, List[str]]
    totalSocialLinks: int
    hasFacebook: str
    hasTwitter: str
    hasLinkedin: str
    hasInstagram: str
    hasYoutube: str
    hasPinterest: str
    hasTiktok: str
    hasWhatsapp: str
    seoScore: int
    seoGrade: str
    status: str
    analyzedAt: str
    error: Optional[str] = None

# Enhanced parallel rate limiter
class ParallelRateLimiter:
    def __init__(self, max_concurrent: int = 20, delay: float = 0.1, burst_limit: int = 50):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.delay = delay
        self.burst_limit = burst_limit
        self.request_times = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        await self.semaphore.acquire()
        
        async with self.lock:
            current_time = time.time()
            
            # Remove old request times (older than 1 second)
            self.request_times = [t for t in self.request_times if current_time - t < 1.0]
            
            # Check burst limit
            if len(self.request_times) >= self.burst_limit:
                sleep_time = 1.0 - (current_time - self.request_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            # Add current request time
            self.request_times.append(current_time)
            
            # Apply minimum delay between requests
            if len(self.request_times) > 1:
                time_since_last = current_time - self.request_times[-2]
                if time_since_last < self.delay:
                    await asyncio.sleep(self.delay - time_since_last)

    def release(self):
        self.semaphore.release()

# Global session pool for better connection reuse
class SessionPool:
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.sessions = []
        self.current_index = 0
        self.lock = asyncio.Lock()
        
    async def get_session(self):
        async with self.lock:
            if not self.sessions:
                # Initialize sessions
                for _ in range(self.pool_size):
                    connector = aiohttp.TCPConnector(
                        limit=100,
                        limit_per_host=20,
                        ttl_dns_cache=300,
                        use_dns_cache=True,
                        ssl=False,
                        enable_cleanup_closed=True,
                        keepalive_timeout=30
                    )
                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=aiohttp.ClientTimeout(total=30, connect=10)
                    )
                    self.sessions.append(session)
            
            # Round-robin session selection
            session = self.sessions[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.sessions)
            return session
    
    async def close_all(self):
        for session in self.sessions:
            await session.close()
        self.sessions = []

# High-throughput worker queue system
class WorkerQueue:
    def __init__(self, max_workers: int = 10, max_queue_size: int = 1000):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.job_queue = asyncio.Queue(maxsize=max_queue_size)
        self.priority_queue = deque()
        self.jobs = {}  # job_id -> JobStatus
        self.workers = []
        self.running = False
        self.stats = {
            'jobs_processed': 0,
            'jobs_failed': 0,
            'total_domains_processed': 0,
            'average_processing_time': 0.0
        }
        
    async def start(self):
        """Start worker processes"""
        if self.running:
            return
        
        self.running = True
        self.workers = [asyncio.create_task(self._worker(i)) for i in range(self.max_workers)]
        logger.info(f"Started {self.max_workers} workers for job processing")
    
    async def stop(self):
        """Stop all workers"""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("All workers stopped")
    
    async def submit_job(self, domains: List[str], batch_size: int = 20, 
                        timeout: int = 15, priority: int = 1, email_priority: List[str] = None) -> str:
        """Submit a new analysis job"""
        job_id = str(uuid.uuid4())
        
        job_status = JobStatus(
            job_id=job_id,
            status='queued',
            total_domains=len(domains),
            processed_domains=0,
            results=[],
            created_at=datetime.now().isoformat()
        )
        
        self.jobs[job_id] = job_status
        
        # Add to appropriate queue based on priority
        job_data = {
            'job_id': job_id,
            'domains': domains,
            'batch_size': batch_size,
            'timeout': timeout,
            'priority': priority,
            'email_priority': email_priority
        }
        
        if priority >= 3:  # High priority
            self.priority_queue.appendleft(job_data)
        else:
            await self.job_queue.put(job_data)
        
        logger.info(f"Job {job_id} submitted with {len(domains)} domains (priority: {priority})")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status by ID"""
        return self.jobs.get(job_id)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        active_jobs = sum(1 for job in self.jobs.values() if job.status == 'processing')
        queued_jobs = sum(1 for job in self.jobs.values() if job.status == 'queued')
        
        return {
            'active_workers': len([w for w in self.workers if not w.done()]),
            'total_workers': self.max_workers,
            'queued_jobs': queued_jobs,
            'active_jobs': active_jobs,
            'queue_size': self.job_queue.qsize(),
            'priority_queue_size': len(self.priority_queue),
            'total_jobs': len(self.jobs),
            **self.stats
        }
    
    async def _worker(self, worker_id: int):
        """Worker process for handling jobs"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Check priority queue first
                job_data = None
                if self.priority_queue:
                    job_data = self.priority_queue.popleft()
                else:
                    # Wait for regular jobs
                    try:
                        job_data = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        continue
                
                if job_data:
                    await self._process_job(worker_id, job_data)
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _process_job(self, worker_id: int, job_data: Dict[str, Any]):
        """Process a single job"""
        job_id = job_data['job_id']
        domains = job_data['domains']
        batch_size = job_data['batch_size']
        timeout = job_data['timeout']
        
        job_status = self.jobs.get(job_id)
        if not job_status:
            return
        
        logger.info(f"Worker {worker_id} processing job {job_id} with {len(domains)} domains")
        
        # Update job status
        job_status.status = 'processing'
        job_status.started_at = datetime.now().isoformat()
        
        start_time = time.time()
        
        try:
            # Process domains using the same parallel approach
            semaphore = asyncio.Semaphore(batch_size)
            
            async def analyze_domain_with_semaphore(domain: str) -> AnalysisResponse:
                async with semaphore:
                    try:
                        return await analyzer.analyze_website(domain, timeout, job_data.get('email_priority'))
                    except asyncio.CancelledError:
                        logger.warning(f"Request cancelled for domain: {domain}")
                        return create_error_response(domain, "Request cancelled")
                    except Exception as e:
                        logger.error(f"Unexpected error for domain {domain}: {e}")
                        return create_error_response(domain, str(e))
            
            # Create all tasks
            tasks = [analyze_domain_with_semaphore(domain) for domain in domains]
            
            # Execute with progress tracking
            results = []
            for i, task in enumerate(asyncio.as_completed(tasks)):
                try:
                    result = await task
                    results.append(result)
                    job_status.processed_domains = i + 1
                except Exception as e:
                    logger.error(f"Task failed in job {job_id}: {e}")
                    job_status.processed_domains = i + 1
            
            # Update job completion - convert AnalysisResponse objects to dictionaries
            job_status.results = [result.dict() if hasattr(result, 'dict') else result for result in results]
            job_status.status = 'completed'
            job_status.completed_at = datetime.now().isoformat()
            
            # Update stats
            processing_time = time.time() - start_time
            self.stats['jobs_processed'] += 1
            self.stats['total_domains_processed'] += len(domains)
            
            # Update average processing time
            current_avg = self.stats['average_processing_time']
            total_jobs = self.stats['jobs_processed']
            self.stats['average_processing_time'] = (
                (current_avg * (total_jobs - 1) + processing_time) / total_jobs
            )
            
            logger.info(f"Worker {worker_id} completed job {job_id} in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Worker {worker_id} failed to process job {job_id}: {e}")
            job_status.status = 'failed'
            job_status.error = str(e)
            job_status.completed_at = datetime.now().isoformat()
            self.stats['jobs_failed'] += 1

# Global instances
rate_limiter = ParallelRateLimiter(max_concurrent=20, delay=0.1, burst_limit=50)
session_pool = SessionPool(pool_size=5)
worker_queue = WorkerQueue(max_workers=10, max_queue_size=1000)

# Website analyzer class
class WebsiteAnalyzer:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Minimal blacklist patterns for email filtering (moved to extract_emails method)
        
        self.generic_usernames = [
            'info', 'admin', 'support', 'contact', 'help', 'sales', 'service',
            'team', 'hello', 'mail', 'email', 'newsletter', 'webmaster'
        ]

    async def fetch_website(self, session: aiohttp.ClientSession, domain: str, timeout: int = 15) -> Dict[str, Any]:
        """Fetch website content with proper error handling, SSL fallback and parallel optimizations"""
        # Try HTTPS first, fallback to HTTP if needed
        urls_to_try = []
        
        if domain.startswith(('http://', 'https://')):
            urls_to_try.append(domain)
        else:
            # Try HTTPS first, then HTTP as fallback
            urls_to_try.extend([f"https://{domain}", f"http://{domain}"])
        
        headers = {
            'User-Agent': self.user_agents[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
        }
        
        last_error = None
        
        for url in urls_to_try:
            try:
                await rate_limiter.acquire()
                
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True,
                    max_redirects=3,
                    compress=True,  # Enable compression handling
                    ssl=False  # Disable SSL verification at request level too
                ) as response:
                    # Try to read content with proper encoding handling
                    try:
                        content = await response.text(encoding='utf-8', errors='ignore')
                    except UnicodeDecodeError:
                        # Fallback to reading as bytes and decode manually
                        raw_content = await response.read()
                        content = raw_content.decode('utf-8', errors='ignore')
                    except Exception as decode_error:
                        # Last resort: try reading without encoding specification
                        try:
                            content = await response.text(errors='ignore')
                        except:
                            logger.warning(f"Failed to decode content for {url}: {decode_error}")
                            content = ""
                    
                    # Success! Return the result
                    return {
                        'content': content,
                        'status_code': response.status,
                        'headers': dict(response.headers),
                        'url': str(response.url),
                        'is_https': str(response.url).startswith('https://'),
                    }
                    
            except asyncio.TimeoutError as e:
                last_error = f'Timeout for {url}'
                logger.warning(f"Timeout accessing {url}")
                continue  # Try next URL
            except aiohttp.ClientError as e:
                last_error = f'Client error for {url}: {str(e)}'
                logger.warning(f"Client error accessing {url}: {e}")
                continue  # Try next URL
            except Exception as e:
                last_error = f'Unexpected error for {url}: {str(e)}'
                logger.warning(f"Unexpected error accessing {url}: {e}")
                continue  # Try next URL
            finally:
                rate_limiter.release()
        
        # If we get here, all URLs failed
        return {
            'error': last_error or f'Failed to access {domain} with any protocol',
            'status_code': 500
        }

    def detect_platform(self, html: str) -> str:
        """Detect website platform"""
        html_lower = html.lower()
        
        if 'wp-content' in html_lower or 'wordpress' in html_lower or '/wp-json/' in html_lower:
            return 'WordPress'
        elif 'shopify' in html_lower or 'cdn.shopify.com' in html_lower:
            return 'Shopify'
        elif 'wix.com' in html_lower or '_wix' in html_lower:
            return 'Wix'
        elif 'squarespace' in html_lower or 'squarespace.com' in html_lower:
            return 'Squarespace'
        elif 'webflow' in html_lower or 'webflow.com' in html_lower:
            return 'Webflow'
        elif 'react' in html_lower or 'next.js' in html_lower or '_next/' in html_lower:
            return 'React/Next.js'
        elif 'drupal' in html_lower:
            return 'Drupal'
        elif 'joomla' in html_lower:
            return 'Joomla'
        elif 'magento' in html_lower or 'mage/' in html_lower:
            return 'Magento'
        else:
            return 'Unknown'

    def extract_emails(self, html: str, email_priority: List[str] = None) -> List[str]:
        """Extract and validate email addresses with enhanced obfuscation handling"""
        # First, handle common obfuscation methods
        processed_html = html
        
        # Decode HTML entities (including numeric)
        import html
        processed_html = html.unescape(processed_html)  # Handle all HTML entities
        
        # Additional manual replacements for common patterns
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
        # Handle cases like <span>user</span>@<span>domain.com</span>
        tag_split_pattern = r'([a-zA-Z0-9._%-]+)</[^>]+>@<[^>]+>([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        processed_html = re.sub(tag_split_pattern, r'\1@\2', processed_html)
        
        # Handle more complex HTML tag splitting like <strong>info</strong>&#64;<strong>domain</strong>&#46;<strong>com</strong>
        # First clean up nested tags around email parts
        nested_pattern = r'<[^>]*>([a-zA-Z0-9._%-]*)</[^>]*>([&#@.]*)<[^>]*>([a-zA-Z0-9._%-]*)</[^>]*>([&#@.]*)<[^>]*>([a-zA-Z0-9._%-]*)</[^>]*>'
        processed_html = re.sub(nested_pattern, r'\1\2\3\4\5', processed_html)
        
        # Handle JavaScript-style string concatenation for emails
        js_concat_pattern = r'"([a-zA-Z0-9._%-]+)"\s*\+\s*"@"\s*\+\s*"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"'
        js_matches = re.findall(js_concat_pattern, processed_html)
        for username, domain in js_matches:
            processed_html += f' {username}@{domain} '  # Add reconstructed email to processed HTML
        
        # Look for emails in form placeholders and values
        form_patterns = [
            r'placeholder=["\']([^"\']*@[^"\']*)["\']',
            r'value=["\']([^"\']*@[^"\']*)["\']',
            r'data-email=["\']([^"\']*@[^"\']*)["\']',
            r'data-contact=["\']([^"\']*@[^"\']*)["\']'
        ]
        
        for pattern in form_patterns:
            form_matches = re.findall(pattern, processed_html, re.IGNORECASE)
            for match in form_matches:
                processed_html += f' {match} '
        
        # Look for emails in JSON-LD structured data and JavaScript objects
        json_patterns = [
            r'"email"\s*:\s*"([^"]*@[^"]*)"',
            r'"contactPoint"\s*:.*?"email"\s*:\s*"([^"]*@[^"]*)"',
            r'email\s*=\s*["\']([^"\']*@[^"\']*)["\']'
        ]
        
        for pattern in json_patterns:
            json_matches = re.findall(pattern, processed_html, re.IGNORECASE)
            for match in json_matches:
                processed_html += f' {match} '
        
        # Handle CloudFlare Email Protection
        cloudflare_emails = self.decode_cloudflare_emails(processed_html)
        for email in cloudflare_emails:
            processed_html += f' {email} '
        
        # More comprehensive email regex
        email_regex = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9._%-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b'
        email_matches = re.findall(email_regex, processed_html, re.IGNORECASE)
        
        # Remove duplicates with enhanced normalization
        unique_emails = []
        seen_emails = set()
        for email in email_matches:
            # Normalize email for duplicate detection
            normalized_email = email.lower().strip()
            
            # Remove common variations that should be considered duplicates
            normalized_email = re.sub(r'^mailto:', '', normalized_email)
            normalized_email = re.sub(r'[<>"\']', '', normalized_email)
            
            if normalized_email not in seen_emails and len(normalized_email) > 0:
                seen_emails.add(normalized_email)
                unique_emails.append(email)
        
        # Clean and filter emails
        cleaned_emails = []
        for email in unique_emails:
            # Clean the email first
            cleaned_email = self.clean_email(email)
            if cleaned_email:
                cleaned_emails.append(cleaned_email)
        
        valid_emails = []
        for email in cleaned_emails:
            if self.is_valid_business_email(email):
                valid_emails.append(email)
                
        # Score and sort emails by quality with priority
        scored_emails = []
        for email in valid_emails:
            score = self.score_email(email, email_priority)
            scored_emails.append((email, score))
            
        scored_emails.sort(key=lambda x: x[1], reverse=True)
        return [email for email, score in scored_emails[:5]]  # Return top 5 to show priority effects

    def clean_email(self, email: str) -> str:
        """Clean email address by removing prefixes, suffixes, and invalid characters"""
        if not email or '@' not in email:
            return ""
            
        email = email.strip()
        
        # Remove Unicode escape sequences like u003e
        email = re.sub(r'u[0-9a-fA-F]{4}', '', email)
        
        # Remove HTML tags and entities that might be around emails
        email = re.sub(r'<[^>]+>', '', email)
        email = email.replace('&lt;', '').replace('&gt;', '')
        email = email.replace('&quot;', '').replace('&#34;', '')
        email = email.replace('&apos;', '').replace('&#39;', '')
        
        # Remove quotes around email
        email = email.strip('\'"')
        
        # Remove common prefixes/suffixes that shouldn't be part of email
        prefixes_to_remove = [
            'mailto:', 'email:', 'contact:', 'send:', 'write:',
            'u003e', 'u003c', '%3e', '%3c',
            '>', '<', ']', '[', ')', '(',
        ]
        
        for prefix in prefixes_to_remove:
            if email.lower().startswith(prefix.lower()):
                email = email[len(prefix):].strip()
            if email.lower().endswith(prefix.lower()):
                email = email[:-len(prefix)].strip()
        
        # Extract just the email part if there's extra text
        email_match = re.search(r'\b[a-zA-Z0-9](?:[a-zA-Z0-9._%-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b', email)
        if email_match:
            email = email_match.group(0)
        
        return email.strip()

    def is_valid_business_email(self, email: str) -> bool:
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
        
        # Extended blacklist of invalid patterns
        invalid_patterns = [
            # File extensions in username
            r'\.(png|jpg|jpeg|gif|svg|webp|ico|css|js|json|xml|pdf|doc|docx|xls|xlsx|zip|rar)$',
            # Generic/placeholder patterns
            r'^(example|test|demo|sample|placeholder|dummy|fake|mock|temp|temporary)@',
            r'^(user|admin|root|guest|anonymous|unknown)@',
            # Domain-only patterns
            r'^(domain|website|site|email|mail|contact|info|support|hello)@$',
            # Numbers-only username (4+ digits)
            r'^[0-9]{4,}$',
            # Very long number sequences (8+ consecutive digits)
            r'[0-9]{8,}',
            # Hash-like patterns (Sentry tracking IDs, etc.)
            r'^[a-f0-9]{16,}@',
            r'^[a-f0-9]{32}@',  # 32-character hex strings (common in tracking)
            r'^[a-f0-9]{24}@',  # 24-character hex strings
            r'^[a-f0-9]{40}@',  # 40-character hex strings
            # UUID-like patterns
            r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}@',
            # Base64-like long strings
            r'^[A-Za-z0-9+/]{20,}@',
            # Tracking/monitoring specific patterns
            r'^(tracking|monitor|analytics|metric|log|debug|error|crash|report).*@.*\.(sentry|bugsnag|rollbar|airbrake)',
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, username):
                return False
        
        # Blacklisted domains
        invalid_domains = [
            # Placeholder domains
            'example.com', 'example.org', 'example.net',
            'test.com', 'test.org', 'test.net',
            'domain.com', 'website.com', 'site.com',
            'email.com', 'mail.com', 'mysite.com',
            'yoursite.com', 'yourdomain.com', 'mydomain.com',
            'company.com', 'business.com', 'sample.com',
            
            # System/tracking domains
            'localhost', '127.0.0.1', 'local.com',
            'sentry.io', 'tracking.com', 'analytics.com',
            'google-analytics.com', 'googletagmanager.com',
            'facebook.com', 'twitter.com', 'instagram.com',
            
            # Sentry and error tracking domains
            'sentry-next.wixpress.com', 'sentry.wixpress.com',
            'bugsnag.com', 'rollbar.com', 'airbrake.io',
            'honeybadger.io', 'raygun.com', 'crashlytics.com',
            
            # Generic patterns
            'noreply.com', 'donotreply.com', 'no-reply.com',
            
            # File-like domains
            'png.com', 'jpg.com', 'gif.com', 'webp.com',
        ]
        
        # Check exact domain matches
        if domain in invalid_domains:
            return False
            
        # Check domain patterns
        invalid_domain_patterns = [
            r'\.(png|jpg|jpeg|gif|svg|webp|ico)$',  # File extensions as TLD
            r'^(example|test|demo|sample|placeholder|dummy|fake)',  # Starts with placeholder
            r'(localhost|127\.0\.0\.1)',  # Local addresses
            r'sentry.*\.wixpress\.com$',  # Sentry tracking domains
            r'.*\.sentry\.io$',  # Sentry.io subdomains
            r'.*\.(bugsnag|rollbar|airbrake|honeybadger|raygun|crashlytics)\.com$',  # Error tracking services
        ]
        
        for pattern in invalid_domain_patterns:
            if re.search(pattern, domain):
                return False
        
        # Additional username validations
        invalid_usernames = [
            # Exact matches
            'example', 'test', 'demo', 'sample', 'placeholder', 'dummy', 'fake',
            'user', 'admin', 'root', 'guest', 'anonymous', 'unknown',
            'domain', 'website', 'site', 'email', 'mail',
            'noreply', 'no-reply', 'donotreply', 'do-not-reply',
            'mailer-daemon', 'postmaster', 'bounce', 'return',
            
            # System accounts (but allow legitimate business emails like 'support', 'info', 'contact')
            'system', 'daemon', 'nobody', 'www', 'ftp', 'apache', 'nginx',
            'mysql', 'postgres', 'redis', 'mongodb',
            
            # Marketing/tracking
            'tracking', 'analytics', 'pixel', 'tag', 'monitor',
            'newsletter', 'marketing',
            'promotion', 'promo', 'deals', 'offer', 'discount',
        ]
        
        # Check if username is in blacklist
        if username in invalid_usernames:
            return False
        
        # Check for suspicious patterns in full email
        suspicious_full_patterns = [
            r'@domain\.com$',  # Literal @domain.com
            r'@email\.com$',   # Literal @email.com
            r'email@domain',   # email@domain pattern
            r'user@domain',    # user@domain pattern
            r'^[^@]+@[^@]+@',  # Multiple @ symbols
            r'\.{2,}',         # Multiple consecutive dots
            r'[<>"\\\[\]]',    # Invalid characters
        ]
        
        for pattern in suspicious_full_patterns:
            if re.search(pattern, email_lower):
                return False
        
        return True

    def score_email(self, email: str, email_priority: List[str] = None) -> int:
        """Score email quality with custom priority"""
        if email_priority is None:
            email_priority = ["info@", "sales@", "@gmail.com"]
        
        score = 100
        email_lower = email.lower()
        username, domain = email_lower.split('@', 1)
        full_email = f"{username}@{domain}"
        
        # Apply priority scoring based on user preferences
        priority_bonus = 0
        for i, priority_pattern in enumerate(email_priority):
            if priority_pattern.startswith('@'):
                # Domain pattern like @gmail.com, @yahoo.com
                if domain == priority_pattern[1:] or domain.endswith(priority_pattern):
                    priority_bonus = 100 - (i * 10)  # Higher bonus for earlier positions
                    break
            elif priority_pattern.endswith('@'):
                # Username pattern like info@, sales@
                pattern_prefix = priority_pattern[:-1]
                if username == pattern_prefix or username.startswith(pattern_prefix):
                    priority_bonus = 100 - (i * 10)  # Higher bonus for earlier positions
                    break
            else:
                # Full email or contains pattern
                if priority_pattern in full_email:
                    priority_bonus = 100 - (i * 10)
                    break
        
        score += priority_bonus
        
        # Penalize generic usernames (less strict)
        if username in self.generic_usernames:
            score -= 20  # Reduced penalty
            
        # Penalize numbers at end (less strict)
        if re.search(r'\d{3,}$', username):  # Only penalize 3+ digits
            score -= 10
            
        # Bonus for personal-looking emails
        if re.match(r'^[a-z]+\.[a-z]+$', username) and len(username) > 3:
            score += 30
            
        # Bonus for non-generic providers (but lower if in priority list)
        generic_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        if domain not in generic_providers:
            score += 25  # Increased bonus for company domains
            
        # Extra bonus for common business email patterns (if not already covered by priority)
        if priority_bonus == 0:  # Only apply if not already prioritized
            if any(pattern in username for pattern in ['contact', 'info', 'sales', 'support', 'hello']):
                score += 15
                
        return score

    def decode_cloudflare_emails(self, html: str) -> List[str]:
        """Decode CloudFlare protected emails from data-cfemail attributes"""
        emails = []
        
        # Find all CloudFlare encrypted emails
        cf_pattern = r'data-cfemail="([a-f0-9]+)"'
        cf_matches = re.findall(cf_pattern, html, re.IGNORECASE)
        
        for encrypted in cf_matches:
            try:
                # CloudFlare email protection algorithm
                # First two characters are the key, rest is the encrypted email
                if len(encrypted) >= 2:
                    key = int(encrypted[:2], 16)
                    encrypted_email = encrypted[2:]
                    
                    # Decode by XORing each pair of hex characters with the key
                    decoded_chars = []
                    for i in range(0, len(encrypted_email), 2):
                        if i + 1 < len(encrypted_email):
                            hex_pair = encrypted_email[i:i+2]
                            char_code = int(hex_pair, 16) ^ key
                            if 32 <= char_code <= 126:  # Printable ASCII
                                decoded_chars.append(chr(char_code))
                    
                    decoded_email = ''.join(decoded_chars)
                    
                    # Validate that it looks like an email
                    if '@' in decoded_email and '.' in decoded_email:
                        emails.append(decoded_email)
                        
            except (ValueError, IndexError):
                # Skip invalid encrypted strings
                continue
        
        return emails

    async def fetch_contact_page_emails(self, session: aiohttp.ClientSession, domain: str, timeout: int = 15, found_contact_pages: List[Dict] = None, email_priority: List[str] = None) -> List[str]:
        """Fetch emails from contact page if homepage has none"""
        contact_emails = []
        
        # Start with detected contact pages from homepage
        contact_urls = []
        if found_contact_pages:
            for page in found_contact_pages:
                contact_urls.append(page['url'])
        
        # Add common contact page URL patterns
        common_patterns = [
            f"https://{domain}/contact",
            f"https://{domain}/contact/",
            f"https://{domain}/contact-us",
            f"https://{domain}/contact-us/",
            f"https://{domain}/get-in-touch",
            f"https://{domain}/reach-out",
            f"https://{domain}/about/contact",
            f"https://{domain}/pages/contact",  # Shopify pattern
            f"http://{domain}/contact",
            f"http://{domain}/contact/",
            f"http://{domain}/contact-us",
        ]
        
        # Add common patterns, avoiding duplicates
        for pattern in common_patterns:
            if pattern not in contact_urls:
                contact_urls.append(pattern)
        
        for contact_url in contact_urls:
            try:
                headers = {
                    'User-Agent': self.user_agents[0],
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
                
                async with session.get(
                    contact_url, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        content = await response.text(errors='ignore')
                        logger.info(f"Successfully fetched contact page: {contact_url}")
                        
                        # Extract emails from contact page
                        page_emails = self.extract_emails(content, email_priority)
                        if page_emails:
                            logger.info(f"Found {len(page_emails)} emails on contact page")
                            contact_emails.extend(page_emails)
                            break  # Stop after finding emails on first working contact page
                    else:
                        logger.debug(f"Contact page returned {response.status}: {contact_url}")
                        
            except Exception as e:
                logger.debug(f"Failed to fetch contact page {contact_url}: {e}")
                continue
        
        # Remove duplicates and return
        return list(set(contact_emails))

    def extract_phones(self, html: str) -> List[str]:
        """Extract and validate phone numbers"""
        phone_regex = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})|(?:\+[1-9]\d{0,3}[-.\s]?)?(?:\([0-9]{1,4}\)[-.\s]?)?[0-9]{1,4}[-.\s]?[0-9]{1,9}'
        phone_matches = re.findall(phone_regex, html)
        
        valid_phones = []
        for match in phone_matches:
            if isinstance(match, tuple):
                phone = ''.join(match)
            else:
                phone = match
                
            clean_phone = re.sub(r'[^\d+]', '', phone)
            
            if (len(clean_phone) >= 10 and len(clean_phone) <= 15 and 
                '1234567890' not in clean_phone and
                not re.match(r'^(\d)\1+$', clean_phone)):
                valid_phones.append(phone)
                
        return list(set(valid_phones))[:2]

    def extract_contact_pages(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract contact page URLs"""
        contact_keywords = [
            'contact', 'contact us', 'contact-us', 'get in touch', 'reach out',
            'connect', 'inquiry', 'support', 'help'
        ]
        
        # Find all anchor tags
        link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        links = re.findall(link_pattern, html, re.IGNORECASE)
        
        contact_pages = []
        for href, text in links:
            text_lower = text.lower().strip()
            href_lower = href.lower()
            
            # Check if this is a contact-related link
            is_contact = (
                'contact' in href_lower or
                any(keyword in text_lower for keyword in contact_keywords)
            )
            
            if is_contact and not any(skip in href for skip in ['mailto:', 'tel:', 'javascript:', '#']):
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = base_url.rstrip('/') + href
                elif not href.startswith(('http://', 'https://')):
                    full_url = base_url.rstrip('/') + '/' + href
                else:
                    full_url = href
                    
                contact_pages.append({
                    'url': full_url,
                    'linkText': text.strip()
                })
                
        # Remove duplicates
        seen_urls = set()
        unique_pages = []
        for page in contact_pages:
            normalized_url = page['url'].rstrip('/')
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_pages.append(page)
                
        return unique_pages

    def extract_social_links(self, html: str) -> Dict[str, List[str]]:
        """Extract social media links"""
        social_patterns = {
            'facebook': r'https?://(?:www\.)?(?:facebook\.com|fb\.com)/[a-zA-Z0-9._-]+',
            'twitter': r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9._-]+',
            'linkedin': r'https?://(?:www\.)?linkedin\.com/(?:in|company)/[a-zA-Z0-9._-]+',
            'instagram': r'https?://(?:www\.)?instagram\.com/[a-zA-Z0-9._-]+',
            'youtube': r'https?://(?:www\.)?(?:youtube\.com/(?:channel/|user/|c/)?|youtu\.be/)[a-zA-Z0-9._-]+',
            'pinterest': r'https?://(?:www\.)?pinterest\.com/[a-zA-Z0-9._-]+',
            'tiktok': r'https?://(?:www\.)?tiktok\.com/@[a-zA-Z0-9._-]+',
            'whatsapp': r'https?://(?:wa\.me|api\.whatsapp\.com)/[0-9]+'
        }
        
        social_links = {}
        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            social_links[platform] = list(set(matches))
            
        return social_links

    def analyze_seo(self, html: str) -> Dict[str, Any]:
        """Analyze SEO elements"""
        # Title analysis
        title_match = re.search(r'<title[^>]*>([^<]*)</title>', html, re.IGNORECASE)
        has_title = bool(title_match)
        title_length = len(title_match.group(1).strip()) if title_match else 0
        title_optimal = 30 <= title_length <= 60
        
        # Meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
        has_description = bool(desc_match)
        desc_length = len(desc_match.group(1).strip()) if desc_match else 0
        desc_optimal = 120 <= desc_length <= 160
        
        # Headers
        has_h1 = bool(re.search(r'<h1[^>]*>', html, re.IGNORECASE))
        h1_count = len(re.findall(r'<h1[^>]*>', html, re.IGNORECASE))
        has_h2 = bool(re.search(r'<h2[^>]*>', html, re.IGNORECASE))
        
        # Technical SEO
        has_viewport = bool(re.search(r'name=["\']viewport["\']', html, re.IGNORECASE))
        has_canonical = bool(re.search(r'rel=["\']canonical["\']', html, re.IGNORECASE))
        has_robots = bool(re.search(r'name=["\']robots["\']', html, re.IGNORECASE))
        has_structured_data = bool(re.search(r'application/ld\+json|schema\.org', html, re.IGNORECASE))
        
        # Social meta tags
        has_og = bool(re.search(r'property=["\']og:', html, re.IGNORECASE))
        has_twitter = bool(re.search(r'name=["\']twitter:', html, re.IGNORECASE))
        
        # Performance
        has_lazy_loading = bool(re.search(r'loading=["\']lazy["\']', html, re.IGNORECASE))
        has_preload = bool(re.search(r'rel=["\']preload["\']', html, re.IGNORECASE))
        
        # Accessibility
        has_alt_tags = bool(re.search(r'alt=', html, re.IGNORECASE))
        has_lang = bool(re.search(r'lang=', html, re.IGNORECASE))
        
        return {
            'hasTitle': 'Yes' if has_title else 'No',
            'titleLength': title_length,
            'titleOptimal': 'Yes' if title_optimal else 'No',
            'hasDescription': 'Yes' if has_description else 'No',
            'descriptionLength': desc_length,
            'descriptionOptimal': 'Yes' if desc_optimal else 'No',
            'hasH1': 'Yes' if has_h1 else 'No',
            'h1Count': h1_count,
            'hasH2': 'Yes' if has_h2 else 'No',
            'hasViewport': 'Yes' if has_viewport else 'No',
            'hasCanonical': 'Yes' if has_canonical else 'No',
            'hasRobots': 'Yes' if has_robots else 'No',
            'hasStructuredData': 'Yes' if has_structured_data else 'No',
            'hasOpenGraph': 'Yes' if has_og else 'No',
            'hasTwitterCard': 'Yes' if has_twitter else 'No',
            'hasLazyLoading': 'Yes' if has_lazy_loading else 'No',
            'hasPreload': 'Yes' if has_preload else 'No',
            'hasAltTags': 'Yes' if has_alt_tags else 'No',
            'hasLang': 'Yes' if has_lang else 'No',
        }

    def calculate_seo_score(self, seo_data: Dict[str, Any]) -> tuple[int, str]:
        """Calculate SEO score and grade"""
        score = 0
        
        if seo_data['hasTitle'] == 'Yes':
            score += 15
        if seo_data['titleOptimal'] == 'Yes':
            score += 10
        if seo_data['hasDescription'] == 'Yes':
            score += 15
        if seo_data['descriptionOptimal'] == 'Yes':
            score += 10
        if seo_data['hasH1'] == 'Yes':
            score += 10
        if seo_data['h1Count'] == 1:
            score += 5
        if seo_data['hasH2'] == 'Yes':
            score += 5
        if seo_data['hasCanonical'] == 'Yes':
            score += 5
        if seo_data['hasOpenGraph'] == 'Yes':
            score += 10
        if seo_data['hasTwitterCard'] == 'Yes':
            score += 5
        if seo_data['hasStructuredData'] == 'Yes':
            score += 10
            
        grade = 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D'
        return score, grade

    async def analyze_website(self, domain: str, timeout: int = 15, email_priority: List[str] = None) -> AnalysisResponse:
        """Main website analysis function with parallel optimizations"""
        try:
            # Use session pool for better connection reuse
            session = await session_pool.get_session()
            
            # Fetch website data
            fetch_result = await self.fetch_website(session, domain, timeout)
                
            if 'error' in fetch_result:
                return AnalysisResponse(
                    domain=domain,
                    platform='Error',
                    purpose='Error',
                    isHttps='No',
                    hasHSTS='No',
                    hasCSP='No',
                    hasXFrameOptions='No',
                    hasTitle='No',
                    titleLength=0,
                    titleOptimal='No',
                    hasDescription='No',
                    descriptionLength=0,
                    descriptionOptimal='No',
                    hasH1='No',
                    h1Count=0,
                    hasH2='No',
                    hasViewport='No',
                    hasCanonical='No',
                    hasRobots='No',
                    hasStructuredData='No',
                    hasOpenGraph='No',
                    hasTwitterCard='No',
                    hasLazyLoading='No',
                    hasPreload='No',
                    hasAltTags='No',
                    hasLang='No',
                    emails=[],
                    emailCount=0,
                    phones=[],
                    phoneCount=0,
                    contactPages=[],
                    contactPageCount=0,
                    hasContactPage='No',
                    socialLinks={},
                    totalSocialLinks=0,
                    hasFacebook='No',
                    hasTwitter='No',
                    hasLinkedin='No',
                    hasInstagram='No',
                    hasYoutube='No',
                    hasPinterest='No',
                    hasTiktok='No',
                    hasWhatsapp='No',
                    seoScore=0,
                    seoGrade='F',
                    status='Error',
                    analyzedAt=datetime.now().isoformat(),
                    error=fetch_result.get('error', 'Unknown error')
                )
                
            html = fetch_result['content']
            headers = fetch_result['headers']
            base_url = fetch_result['url']
            
            # Platform detection
            platform = self.detect_platform(html)
            
            # Security analysis
            is_https = 'Yes' if fetch_result['is_https'] else 'No'
            has_hsts = 'Yes' if 'strict-transport-security' in headers else 'No'
            has_csp = 'Yes' if 'content-security-policy' in headers else 'No'
            has_xframe = 'Yes' if 'x-frame-options' in headers else 'No'
            
            # SEO analysis
            seo_data = self.analyze_seo(html)
            seo_score, seo_grade = self.calculate_seo_score(seo_data)
            
            # Contact information - try homepage first
            emails = self.extract_emails(html, email_priority)
            phones = self.extract_phones(html)
            contact_pages = self.extract_contact_pages(html, base_url)
            
            # If no emails found on homepage, try contact pages
            if not emails:
                logger.info(f"No emails found on homepage of {domain}, trying contact pages...")
                contact_emails = await self.fetch_contact_page_emails(session, domain, timeout, contact_pages, email_priority)
                emails.extend(contact_emails)
            
            # Social media
            social_links = self.extract_social_links(html)
            total_social = sum(len(links) for links in social_links.values())
            
            return AnalysisResponse(
                domain=domain,
                platform=platform,
                purpose='General',  # Could be enhanced with more sophisticated detection
                isHttps=is_https,
                hasHSTS=has_hsts,
                hasCSP=has_csp,
                hasXFrameOptions=has_xframe,
                emails=emails,
                emailCount=len(emails),
                phones=phones,
                phoneCount=len(phones),
                contactPages=contact_pages,
                contactPageCount=len(contact_pages),
                hasContactPage='Yes' if contact_pages else 'No',
                socialLinks=social_links,
                totalSocialLinks=total_social,
                hasFacebook='Yes' if social_links.get('facebook') else 'No',
                hasTwitter='Yes' if social_links.get('twitter') else 'No',
                hasLinkedin='Yes' if social_links.get('linkedin') else 'No',
                hasInstagram='Yes' if social_links.get('instagram') else 'No',
                hasYoutube='Yes' if social_links.get('youtube') else 'No',
                hasPinterest='Yes' if social_links.get('pinterest') else 'No',
                hasTiktok='Yes' if social_links.get('tiktok') else 'No',
                hasWhatsapp='Yes' if social_links.get('whatsapp') else 'No',
                seoScore=seo_score,
                seoGrade=seo_grade,
                status='Active' if fetch_result['status_code'] == 200 else f'Not Accessible ({fetch_result["status_code"]})',
                analyzedAt=datetime.now().isoformat(),
                **seo_data
            )
                
        except Exception as e:
            logger.error(f"Error analyzing {domain}: {str(e)}")
            return AnalysisResponse(
                domain=domain,
                platform='Error',
                purpose='Error',
                isHttps='No',
                hasHSTS='No',
                hasCSP='No',
                hasXFrameOptions='No',
                hasTitle='No',
                titleLength=0,
                titleOptimal='No',
                hasDescription='No',
                descriptionLength=0,
                descriptionOptimal='No',
                hasH1='No',
                h1Count=0,
                hasH2='No',
                hasViewport='No',
                hasCanonical='No',
                hasRobots='No',
                hasStructuredData='No',
                hasOpenGraph='No',
                hasTwitterCard='No',
                hasLazyLoading='No',
                hasPreload='No',
                hasAltTags='No',
                hasLang='No',
                emails=[],
                emailCount=0,
                phones=[],
                phoneCount=0,
                contactPages=[],
                contactPageCount=0,
                hasContactPage='No',
                socialLinks={},
                totalSocialLinks=0,
                hasFacebook='No',
                hasTwitter='No',
                hasLinkedin='No',
                hasInstagram='No',
                hasYoutube='No',
                hasPinterest='No',
                hasTiktok='No',
                hasWhatsapp='No',
                seoScore=0,
                seoGrade='F',
                status='Analysis Failed',
                analyzedAt=datetime.now().isoformat(),
                error=str(e)
            )

# Initialize analyzer
analyzer = WebsiteAnalyzer()

def create_error_response(domain: str, error_message: str) -> AnalysisResponse:
    """Create a standardized error response with all required fields"""
    return AnalysisResponse(
        domain=domain,
        platform='Error',
        purpose='Error',
        isHttps='No',
        hasHSTS='No',
        hasCSP='No',
        hasXFrameOptions='No',
        hasTitle='No',
        titleLength=0,
        titleOptimal='No',
        hasDescription='No',
        descriptionLength=0,
        descriptionOptimal='No',
        hasH1='No',
        h1Count=0,
        hasH2='No',
        hasViewport='No',
        hasCanonical='No',
        hasRobots='No',
        hasStructuredData='No',
        hasOpenGraph='No',
        hasTwitterCard='No',
        hasLazyLoading='No',
        hasPreload='No',
        hasAltTags='No',
        hasLang='No',
        emails=[],
        emailCount=0,
        phones=[],
        phoneCount=0,
        contactPages=[],
        contactPageCount=0,
        hasContactPage='No',
        socialLinks={},
        totalSocialLinks=0,
        hasFacebook='No',
        hasTwitter='No',
        hasLinkedin='No',
        hasInstagram='No',
        hasYoutube='No',
        hasPinterest='No',
        hasTiktok='No',
        hasWhatsapp='No',
        seoScore=0,
        seoGrade='F',
        status='Error',
        analyzedAt=datetime.now().isoformat(),
        error=error_message
    )

@app.post("/analyze", response_model=List[AnalysisResponse])
async def analyze_websites(request: AnalysisRequest):
    """Analyze multiple websites with optimized parallel processing"""
    results = []
    
    # Enhanced batch processing for better parallelism
    batch_size = min(request.batch_size, 50)  # Increased max batch size
    total_domains = len(request.domains)
    
    logger.info(f"Starting analysis of {total_domains} domains with batch size {batch_size}")
    
    # Process all domains in parallel with controlled concurrency
    semaphore = asyncio.Semaphore(batch_size)
    
    async def analyze_domain_with_semaphore(domain: str) -> AnalysisResponse:
        async with semaphore:
            try:
                return await analyzer.analyze_website(domain, request.timeout, request.email_priority)
            except asyncio.CancelledError:
                logger.warning(f"Request cancelled for domain: {domain}")
                return create_error_response(domain, "Request cancelled")
            except Exception as e:
                logger.error(f"Unexpected error for domain {domain}: {e}")
                return create_error_response(domain, str(e))
    
    # Create all tasks at once for maximum parallelism
    tasks = [analyze_domain_with_semaphore(domain) for domain in request.domains]
    
    # Execute all tasks concurrently
    start_time = time.time()
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    # Process results
    successful_results = 0
    failed_results = 0
    
    for result in batch_results:
        if isinstance(result, Exception):
            logger.error(f"Exception in parallel processing: {result}")
            failed_results += 1
            continue
        results.append(result)
        successful_results += 1
    
    # Log performance metrics
    total_time = end_time - start_time
    avg_time_per_domain = total_time / total_domains if total_domains > 0 else 0
    
    logger.info(f"Analysis completed: {successful_results} successful, {failed_results} failed, "
               f"total time: {total_time:.2f}s, avg per domain: {avg_time_per_domain:.2f}s")
    
    return results

@app.post("/analyze-batch", response_model=List[AnalysisResponse])
async def analyze_websites_batch(request: AnalysisRequest):
    """Analyze multiple websites with traditional batch processing (for comparison)"""
    results = []
    
    # Traditional batch processing
    batch_size = min(request.batch_size, 20)
    
    for i in range(0, len(request.domains), batch_size):
        batch = request.domains[i:i + batch_size]
        
        # Process batch concurrently with error handling
        async def analyze_with_error_handling(domain: str) -> AnalysisResponse:
            try:
                return await analyzer.analyze_website(domain, request.timeout, request.email_priority)
            except asyncio.CancelledError:
                logger.warning(f"Request cancelled for domain: {domain}")
                return create_error_response(domain, "Request cancelled")
            except Exception as e:
                logger.error(f"Unexpected error for domain {domain}: {e}")
                return create_error_response(domain, str(e))
        
        tasks = [analyze_with_error_handling(domain) for domain in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Exception in batch processing: {result}")
                continue
            results.append(result)
        
        # Small delay between batches
        if i + batch_size < len(request.domains):
            await asyncio.sleep(0.2)
    
    return results

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Website Analysis API",
        "version": "2.0.0",
        "description": "High-performance Python API for website analysis and scraping with parallel processing and job queues",
        "features": {
            "parallel_processing": "Optimized concurrent analysis with asyncio.gather",
            "connection_pooling": "Reusable HTTP sessions with round-robin selection",
            "advanced_rate_limiting": "Burst handling with adaptive delays",
            "session_management": "Connection pool for better performance",
            "job_queue_system": "Background processing for large batches",
            "priority_queues": "High-priority job processing",
            "real_time_stats": "Performance monitoring and metrics"
        },
        "endpoints": {
            "POST /analyze": "Analyze multiple websites (parallel optimized)",
            "POST /analyze-batch": "Analyze multiple websites (traditional batching)",
            "POST /jobs/submit": "Submit job for background processing",
            "GET /jobs/{job_id}/status": "Get job status",
            "GET /jobs/{job_id}/results": "Get job results",
            "GET /queue/stats": "Worker queue statistics",
            "GET /health": "Health check",
            "GET /performance": "Performance metrics",
            "GET /docs": "API documentation"
        },
        "usage_recommendations": {
            "small_batches": "Use POST /analyze for <100 domains",
            "large_batches": "Use POST /jobs/submit for >100 domains",
            "optimal_batch_size": "20-50 domains per request",
            "high_priority": "Set priority=3 for urgent jobs"
        },
        "email_priority_feature": {
            "description": "Customize email discovery priority with email_priority parameter",
            "default_priority": ["info@", "sales@", "@gmail.com"],
            "pattern_types": {
                "username_patterns": "info@, sales@, contact@ - matches email prefixes",
                "domain_patterns": "@gmail.com, @yahoo.com - matches email domains", 
                "contains_patterns": "support, business - matches text anywhere in email"
            },
            "examples": {
                "b2b_lead_generation": ["sales@", "business@", "info@"],
                "customer_support": ["support@", "help@", "service@"],
                "executive_contact": ["ceo@", "founder@", "president@"],
                "personal_outreach": ["@gmail.com", "@yahoo.com", "@hotmail.com"]
            }
        }
    }

# Worker queue endpoints
@app.post("/jobs/submit", response_model=Dict[str, str])
async def submit_analysis_job(request: AnalysisJobRequest):
    """Submit a job for background processing"""
    job_id = await worker_queue.submit_job(
        domains=request.domains,
        batch_size=request.batch_size,
        timeout=request.timeout,
        priority=request.priority,
        email_priority=request.email_priority
    )
    
    return {"job_id": job_id, "status": "submitted"}

@app.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status by ID"""
    job_status = worker_queue.get_job_status(job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_status

@app.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    """Get job results by ID"""
    job_status = worker_queue.get_job_status(job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_status.status != 'completed':
        return {
            "job_id": job_id,
            "status": job_status.status,
            "message": f"Job is {job_status.status}. Results not yet available."
        }
    
    return {
        "job_id": job_id,
        "status": job_status.status,
        "total_domains": job_status.total_domains,
        "processed_domains": job_status.processed_domains,
        "results": job_status.results
    }

@app.get("/queue/stats")
async def get_queue_stats():
    """Get worker queue statistics"""
    return worker_queue.get_queue_stats()

@app.get("/performance")
async def performance_metrics():
    """Get current performance metrics"""
    queue_stats = worker_queue.get_queue_stats()
    
    return {
        "rate_limiter": {
            "max_concurrent": rate_limiter.semaphore._value,
            "current_requests": len(rate_limiter.request_times),
            "delay": rate_limiter.delay,
            "burst_limit": rate_limiter.burst_limit
        },
        "session_pool": {
            "pool_size": session_pool.pool_size,
            "active_sessions": len(session_pool.sessions),
            "current_index": session_pool.current_index
        },
        "worker_queue": queue_stats,
        "recommendations": {
            "optimal_batch_size": "20-50 domains for best performance",
            "max_concurrent_requests": "20 requests per second",
            "timeout_recommendation": "15-30 seconds per domain",
            "use_job_queue": "For large batches (>100 domains), use /jobs/submit endpoint"
        }
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    await worker_queue.start()
    logger.info("Worker queue system started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    await worker_queue.stop()
    await session_pool.close_all()
    logger.info("All resources cleaned up")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", access_log=True, workers=1)