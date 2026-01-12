"""Base scraper class with rate limiting, robots.txt checking, and HTML caching."""
import asyncio
import time
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright, TimeoutError as PlaywrightTimeoutError
import aiohttp
import config


class BaseScraper:
    """Base class for all store scrapers with common functionality."""
    
    def __init__(self, store_name: str, base_url: str):
        self.store_name = store_name
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.last_request_time = 0.0
        self.rate_limit = config.RATE_LIMIT_PER_DOMAIN
        self.robots_parser = None
        self.cache_dir = config.CACHE_DIR / self.store_name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Playwright] = None
        
    async def _check_robots_txt(self):
        """Check and parse robots.txt for the domain."""
        robots_url = urljoin(self.base_url, "/robots.txt")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content = await response.text()
                        self.robots_parser = RobotFileParser()
                        self.robots_parser.set_url(robots_url)
                        # Parse content - parse() expects an iterable of lines
                        self.robots_parser.read = lambda: None  # Prevent automatic fetch
                        self.robots_parser.parse(content.splitlines())
                        print(f"[OK] Loaded robots.txt for {self.domain}")
                    else:
                        print(f"[WARNING] robots.txt not found for {self.domain} (status {response.status})")
        except Exception as e:
            print(f"[WARNING] Could not load robots.txt for {self.domain}: {e}")
            # Default to allowing all if robots.txt is unavailable
            self.robots_parser = None
    
    def _is_allowed_url(self, url: str) -> bool:
        """Check if URL is allowed (not checkout, cart, or account pages)."""
        url_lower = url.lower()
        blocked_paths = ['/checkout', '/cart', '/basket', '/account', '/login', '/register', 
                         '/signin', '/signup', '/profile', '/my-account', '/user']
        return not any(path in url_lower for path in blocked_paths)
    
    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt and URL filtering."""
        # First check if URL is in blocked paths (checkout, cart, account)
        if not self._is_allowed_url(url):
            return False
        
        # Then check robots.txt
        if self.robots_parser is None:
            return True
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        return self.robots_parser.can_fetch(user_agent, url)
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for a URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.html"
    
    def _load_from_cache(self, url: str) -> Optional[str]:
        """Load HTML from cache if available."""
        if not config.ENABLE_CACHE:
            return None
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"[WARNING] Error reading cache for {url}: {e}")
        return None
    
    def _save_to_cache(self, url: str, html: str):
        """Save HTML to cache."""
        if not config.ENABLE_CACHE:
            return
        cache_path = self._get_cache_path(url)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print(f"[WARNING] Error saving cache for {url}: {e}")
    
    async def _fetch_page(self, url: str, use_cache: bool = True) -> Optional[str]:
        """Fetch a page with rate limiting, robots.txt checking, and caching."""
        # Check robots.txt and URL filtering
        if not self._can_fetch(url):
            if not self._is_allowed_url(url):
                print(f"[BLOCKED] URL (checkout/cart/account): {url}")
            else:
                print(f"[BLOCKED] robots.txt: {url}")
            return None
        
        # Check cache first
        if use_cache:
            cached_html = self._load_from_cache(url)
            if cached_html:
                print(f"[OK] Using cached: {url}")
                return cached_html
        
        # Rate limiting
        await self._rate_limit()
        
        # Fetch page
        try:
            if self.browser is None:
                raise RuntimeError("Browser not initialized. Call init_browser() first.")
            
            page = await self.browser.new_page()
            # Set realistic user agent and viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })
            await page.goto(url, wait_until="networkidle", timeout=config.TIMEOUT)
            html = await page.content()
            await page.close()
            
            # Save to cache
            self._save_to_cache(url, html)
            print(f"[OK] Fetched: {url}")
            return html
            
        except PlaywrightTimeoutError:
            print(f"[ERROR] Timeout fetching: {url}")
            return None
        except Exception as e:
            print(f"[ERROR] Error fetching {url}: {e}")
            import traceback
            if not config.HEADLESS:  # Only show full traceback in non-headless mode
                traceback.print_exc()
            return None
    
    async def init_browser(self):
        """Initialize Playwright browser with realistic user agent."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=config.HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )
        print(f"[OK] Browser initialized for {self.store_name}")
    
    async def close_browser(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        print(f"[OK] Browser closed for {self.store_name}")
    
    async def scrape_products(self) -> List[Dict]:
        """
        Main scraping method to be implemented by subclasses.
        Returns a list of product dictionaries with normalized fields.
        """
        raise NotImplementedError("Subclasses must implement scrape_products()")
    
    def normalize_product(self, raw_product: Dict) -> Dict:
        """
        Normalize product data to common schema.
        To be overridden by subclasses if needed.
        """
        return {
            "store": self.store_name,
            "store_product_id": raw_product.get("id", ""),
            "url": raw_product.get("url", ""),
            "name": raw_product.get("name", ""),
            "description": raw_product.get("description", ""),
            "category": raw_product.get("category", ""),
            "brand": raw_product.get("brand", ""),
            "price": float(raw_product.get("price", 0)),
            "currency": raw_product.get("currency", "EUR"),
            "original_price": raw_product.get("original_price"),
            "discount_percentage": raw_product.get("discount_percentage"),
            "image_url": raw_product.get("image_url", ""),
            "availability": raw_product.get("availability", "unknown"),
            "specifications": json.dumps(raw_product.get("specifications", {}))
        }
