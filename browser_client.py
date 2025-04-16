"""
Browser client for fetching pages and extracting download links.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Set

import playwright.async_api as pw

from harvester.extractor import extract_download_url


class RateLimiter:
    """Rate limiter to prevent overloading the target server."""
    
    def __init__(self, delay_between_requests: int, max_requests_per_minute: int):
        """
        Initialize the rate limiter.
        
        Args:
            delay_between_requests: Minimum delay between requests in seconds
            max_requests_per_minute: Maximum number of requests per minute
        """
        self.delay_between_requests = delay_between_requests
        self.max_requests_per_minute = max_requests_per_minute
        self.request_times: List[float] = []
        self.lock = asyncio.Lock()
    
    async def wait_for_request(self) -> None:
        """Wait for the appropriate time to make the next request."""
        async with self.lock:
            current_time = time.time()
            
            # Remove request times older than 60 seconds
            one_minute_ago = current_time - 60
            self.request_times = [t for t in self.request_times if t > one_minute_ago]
            
            # If we've hit the rate limit, wait until we can make another request
            if len(self.request_times) >= self.max_requests_per_minute:
                oldest_time = min(self.request_times)
                sleep_time = max(60 - (current_time - oldest_time), 0)
                await asyncio.sleep(sleep_time)
            
            # Apply the minimum delay between requests
            if self.request_times:
                latest_time = max(self.request_times)
                elapsed = current_time - latest_time
                if elapsed < self.delay_between_requests:
                    await asyncio.sleep(self.delay_between_requests - elapsed)
            
            # Record this request time
            self.request_times.append(time.time())


class BrowserClient:
    """Client for interacting with the browser to fetch pages and extract download links."""
    
    def __init__(
        self, 
        delay_between_requests: int = 5, 
        max_requests_per_minute: int = 10,
        timeout: int = 15,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the browser client.
        
        Args:
            delay_between_requests: Minimum delay between requests in seconds
            max_requests_per_minute: Maximum number of requests per minute
            timeout: Timeout for waiting for download link in seconds
            logger: Logger instance
        """
        self.rate_limiter = RateLimiter(delay_between_requests, max_requests_per_minute)
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self.browser = None
        self.context = None
        self.xhr_responses: Dict[str, str] = {}
    
    async def initialize(self) -> None:
        """Initialize the Playwright browser."""
        self.logger.info("Initializing headless browser")
        playwright = await pw.async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        )
        self.logger.info("Browser initialized")
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
            self.logger.info("Browser closed")
    
    async def fetch_and_extract(self, url: str) -> Optional[str]:
        """
        Fetch a page and extract the download URL.
        
        Args:
            url: URL of the page to fetch
            
        Returns:
            The download URL if found, None otherwise
        """
        # Wait for rate limiting
        await self.rate_limiter.wait_for_request()
        
        if not self.browser or not self.context:
            await self.initialize()
        
        # Clear XHR responses for this request
        self.xhr_responses.clear()
        
        # Create a new page
        page = await self.context.new_page()
        
        try:
            # Set up XHR interception
            page.on("response", lambda response: asyncio.create_task(
                self._handle_response(response)
            ))
            
            self.logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
            
            # Wait for network activity to settle
            await asyncio.sleep(2)
            
            # Extract the download URL
            download_url = await extract_download_url(
                page, 
                self.xhr_responses, 
                self.timeout
            )
            
            return download_url
        except Exception as e:
            self.logger.error(f"Error while processing {url}: {e}")
            return None
        finally:
            await page.close()
    
    async def _handle_response(self, response: pw.Response) -> None:
        """
        Handle an XHR response.
        
        Args:
            response: The response object from Playwright
        """
        if response.request.resource_type in ["fetch", "xhr", "media"]:
            try:
                url = response.url
                
                # Only store responses that might contain video URLs
                if any(pattern in url for pattern in [
                    "m3u8", "mpd", "video", "media", "stream", "mp4", "download"
                ]):
                    # Store the URL for potential analysis
                    self.xhr_responses[url] = url
                    self.logger.debug(f"Intercepted XHR: {url}")
            except Exception as e:
                self.logger.debug(f"Error handling response: {e}")
