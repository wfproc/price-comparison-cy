"""Scraper for Public Cyprus (public.cy)."""
import re
import gzip
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from urllib.parse import urljoin, urlparse
import aiohttp


class PublicScraper(BaseScraper):
    """Scraper for Public Cyprus website."""

    def __init__(self):
        super().__init__(
            store_name="public",
            base_url="https://www.public.cy/"
        )
        self.sitemap_url = "https://www.public.cy/sitemap/sitemap_public_categories.xml.gz"
        self.visited_urls: Set[str] = set()
        self.category_queue: List[str] = []
        self.category_filter: Optional[List[str]] = None
        self.category_keywords: Dict[str, List[str]] = {}

        # Fallback URLs if sitemap is not accessible
        self.fallback_category_urls = {
            "smartphones": [
                "https://www.public.cy/",  # Homepage often has smartphones
            ],
            "laptops": [
                "https://www.public.cy/",
            ],
            "gaming": [
                "https://www.public.cy/",
            ],
            "tablets": [
                "https://www.public.cy/",
            ],
        }

    def set_category_filter(self, categories: List[str], category_keywords: Dict[str, List[str]]):
        """
        Set category filter to limit scraping to specific categories.

        Args:
            categories: List of category names to scrape (e.g., ["smartphones", "laptops"])
            category_keywords: Dict mapping category names to URL keywords to match
        """
        self.category_filter = categories
        self.category_keywords = category_keywords
        print(f"[INFO] Category filter set: {', '.join(categories)}")

    def _matches_category_filter(self, url: str) -> bool:
        """
        Check if a URL matches the category filter.

        Args:
            url: URL to check

        Returns:
            True if URL matches filter (or no filter set), False otherwise
        """
        if not self.category_filter:
            return True  # No filter, allow all

        url_lower = url.lower()

        # Check if URL contains any keywords for selected categories
        for category in self.category_filter:
            keywords = self.category_keywords.get(category, [])
            for keyword in keywords:
                if keyword in url_lower:
                    return True

        return False
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text string."""
        if not text:
            return None
        # Remove currency symbols and whitespace
        text = text.replace('\u20ac', '').replace('EUR', '').replace(' ', '').strip()
        
        # Handle European format (1.234,56) vs US format (1,234.56)
        # If there's a comma followed by 2 digits at the end, it's likely European format
        if re.search(r',\d{2}$', text):
            # European format: 1.234,56 -> 1234.56
            text = text.replace('.', '').replace(',', '.')
        else:
            # US format or simple: 1234.56 or 1234,56 -> 1234.56
            text = text.replace(',', '')
        
        # Extract number (including decimal)
        price_match = re.search(r'(\d+\.?\d*)', text)
        if price_match:
            try:
                price = float(price_match.group(1))
                # Sanity check: prices should be reasonable (between 1 and 1,000,000)
                if 1 <= price <= 1000000:
                    return price
            except ValueError:
                pass
        return None

    def _extract_price_from_element(self, elem) -> Optional[float]:
        """Extract price from a BeautifulSoup element if present."""
        if not elem:
            return None
        return self._extract_price(elem.get_text(strip=True))

    async def _fetch_sitemap_urls(self) -> List[str]:
        """Fetch and parse the sitemap XML.gz file to get all category URLs."""
        urls = []

        # First try with aiohttp (faster)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.sitemap_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.read()

                        # Try to decompress, if it fails it might not be gzipped
                        try:
                            decompressed = gzip.decompress(content)
                        except gzip.BadGzipFile:
                            print("[INFO] Sitemap is not gzipped, using raw content")
                            decompressed = content

                        # Parse XML
                        root = ET.fromstring(decompressed)
                        # XML namespace for sitemap
                        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                        # Extract all <loc> elements
                        for loc in root.findall('.//sm:loc', ns):
                            url = loc.text
                            if url:
                                urls.append(url)
                        print(f"[OK] Loaded {len(urls)} URLs from sitemap")
                        return urls
                    else:
                        print(f"[WARNING] Sitemap fetch failed with status {response.status}, will try with browser")
        except Exception as e:
            print(f"[WARNING] aiohttp sitemap fetch failed: {e}, will try with browser")

        # If aiohttp fails, try with browser (bypasses anti-bot)
        try:
            if not self.browser:
                await self.init_browser()

            print("[INFO] Fetching sitemap using browser...")
            page = await self.context.new_page()

            # Import config for timeout
            import config as cfg

            # Fetch sitemap with browser
            response = await page.goto(self.sitemap_url, timeout=cfg.TIMEOUT, wait_until="domcontentloaded")

            if response and response.status == 200:
                # Get the raw content
                content = await page.content()

                # The content will be wrapped in HTML, extract the text
                soup = BeautifulSoup(content, 'lxml')
                # Get text content (sitemap XML)
                xml_text = soup.get_text()

                # Try to parse as XML
                try:
                    root = ET.fromstring(xml_text.encode('utf-8'))
                    # XML namespace for sitemap
                    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                    # Extract all <loc> elements
                    for loc in root.findall('.//sm:loc', ns):
                        url = loc.text
                        if url:
                            urls.append(url)
                    print(f"[OK] Loaded {len(urls)} URLs from sitemap using browser")
                except Exception as parse_error:
                    print(f"[WARNING] Could not parse sitemap XML: {parse_error}")
            else:
                status = response.status if response else "no response"
                print(f"[WARNING] Browser sitemap fetch failed with status {status}")

            await page.close()

        except Exception as e:
            print(f"[WARNING] Browser sitemap fetch failed: {e}")

        return urls

    def _parse_product_card(self, card_element, base_url: str) -> Optional[Dict]:
        """Parse a product card element into a product dictionary."""
        try:
            # Extract product link
            link_elem = card_element.find('a', href=True)
            if not link_elem:
                return None

            product_url = urljoin(base_url, link_elem['href'])

            # Filter out blocked URLs (checkout, cart, account pages)
            if not self._is_allowed_url(product_url):
                return None

            # Extract product name - try multiple strategies
            name = ""
            # Strategy 1: Look for title elements
            name_elem = card_element.select_one('h2, h3, h4, .product-title, .product__title, .product-name, [class*="title"]')
            if name_elem:
                name = name_elem.get_text(strip=True)

            # Strategy 2: Look for text in the link
            if not name:
                name = link_elem.get_text(strip=True)

            # Strategy 3: Extract from URL if it contains product name
            if not name or len(name) < 3:
                # URL format: /product/category/.../product-name-slug/ID
                url_parts = product_url.split('/')
                if len(url_parts) > 2:
                    # Get the last part before the ID (product name slug)
                    name_slug = url_parts[-2] if url_parts[-1].isdigit() else url_parts[-1]
                    # Convert slug to readable name
                    name = name_slug.replace('-', ' ').title()

            # Strategy 4: Look for any text in the container
            if not name or len(name) < 3:
                container_text = card_element.get_text(strip=True)
                # Take first meaningful line
                lines = [l.strip() for l in container_text.split('\n') if l.strip() and len(l.strip()) > 3]
                if lines:
                    name = lines[0][:200]  # Limit length

            # Extract price - look in multiple places
            price = None
            price_elem = card_element.select_one('.product__price--final, [class*="product__price"]')
            price = self._extract_price_from_element(price_elem)
            # If no price found, search in all text within container
            if not price:
                container_text = card_element.get_text()
                price_patterns = [
                    r'([\d,]+\.?\d*)\s*EUR',
                    r'EUR\s*([\d,]+\.?\d*)'
                ]
                for pattern in price_patterns:
                    match = re.search(pattern, container_text, re.IGNORECASE)
                    if match:
                        price = self._extract_price(match.group(1))
                        if price:
                            break

            # Extract original price (for discounts)
            original_price_elem = card_element.select_one('.product__price--initial, .original-price, .old-price, .product__price, [class*="original"], [class*="old"]')
            original_price = self._extract_price_from_element(original_price_elem)

            # Calculate discount percentage
            discount_percentage = None
            if original_price and price:
                discount_percentage = ((original_price - price) / original_price) * 100

            # Extract image
            img_elem = card_element.find('img', src=True)
            image_url = ""
            if img_elem:
                image_url = urljoin(base_url, img_elem.get('src', ''))

            # Extract product ID from URL or data attributes
            product_id = ""
            if 'data-product-id' in card_element.attrs:
                product_id = card_element['data-product-id']
            elif 'data-id' in card_element.attrs:
                product_id = card_element['data-id']
            else:
                # Try to extract from URL - Public.cy format: /product/.../1234567
                url_match = re.search(r'/product/[^/]+/(\d+)$|/product/(\d+)|/p/(\d+)|id=(\d+)', product_url)
                if url_match:
                    product_id = url_match.group(1) or url_match.group(2) or url_match.group(3) or url_match.group(4)

            # Extract brand (often in name or separate element)
            brand = ""
            brand_elem = card_element.find(['.brand', '[class*="brand"]'])
            if brand_elem:
                brand = brand_elem.get_text(strip=True)
            else:
                # Try to extract from name (first word often brand)
                name_parts = name.split()
                if name_parts:
                    brand = name_parts[0]

            # Availability
            availability = "unknown"
            availability_elem = card_element.select_one('.availability, .stock, [class*="stock"], [class*="available"]')
            if availability_elem:
                availability_text = availability_elem.get_text(strip=True).lower()
                if 'out' in availability_text or 'unavailable' in availability_text:
                    availability = "out_of_stock"
                elif 'in stock' in availability_text or 'available' in availability_text:
                    availability = "in_stock"
                elif 'pre-order' in availability_text or 'preorder' in availability_text:
                    availability = "pre_order"

            # Name is required, but price might be on product page
            if not name:
                return None

            # If no price found, set to 0 (will need to fetch product page later)
            if not price:
                price = 0.0

            return {
                "id": product_id or product_url,
                "url": product_url,
                "name": name,
                "description": "",
                "category": "",
                "brand": brand,
                "price": price,
                "currency": "EUR",
                "original_price": original_price,
                "discount_percentage": discount_percentage,
                "image_url": image_url,
                "availability": availability,
                "specifications": {}
            }
        except Exception as e:
            print(f"[WARNING] Error parsing product card: {e}")
            return None

    async def _fetch_product_details(self, product_url: str) -> Optional[Dict]:
        """Fetch price and details from individual product page."""
        try:
            html = await self._fetch_page(product_url)
            if not html:
                return None

            soup = BeautifulSoup(html, 'lxml')

            # Extract price from product page
            initial_elem = soup.select_one('.product__price--initial')
            final_elem = soup.select_one('.product__price--final')
            original_price = self._extract_price_from_element(initial_elem)
            price = self._extract_price_from_element(final_elem)

            if not price:
                price_elem = soup.select_one('.product__price')
                price = self._extract_price_from_element(price_elem)
            # If still no price, search in all text
            if not price:
                page_text = soup.get_text()
                price_patterns = [
                    r'([\d,]+\.?\d*)\s*EUR',
                    r'EUR\s*([\d,]+\.?\d*)',
                    r'price["\']?\s*[:=]\s*([\d,]+\.?\d*)',
                ]
                for pattern in price_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        price = self._extract_price(match.group(1))
                        if price and price > 0:  # Valid price
                            break

            # If no price found and cache might be stale, refetch once without cache
            if not price:
                html = await self._fetch_page(product_url, use_cache=False)
                if html:
                    soup = BeautifulSoup(html, 'lxml')
                    initial_elem = soup.select_one('.product__price--initial')
                    final_elem = soup.select_one('.product__price--final')
                    original_price = self._extract_price_from_element(initial_elem)
                    price = self._extract_price_from_element(final_elem)
                    if not price:
                        price_elem = soup.select_one('.product__price')
                        price = self._extract_price_from_element(price_elem)
                    if not original_price:
                        original_price_elem = soup.select_one('.original-price, .old-price, [class*="original-price"], [class*="old-price"]')
                        original_price = self._extract_price_from_element(original_price_elem)

            # Extract description
            description = ""
            desc_selectors = ['.description', '.product-description', '[class*="description"]', '[itemprop="description"]']
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)[:1000]  # Limit length
                    break

            # Extract original price for discounts (fallback if initial not found)
            if not original_price:
                original_price_elem = soup.select_one('.original-price, .old-price, [class*="original-price"], [class*="old-price"]')
                original_price = self._extract_price_from_element(original_price_elem)

            return {
                "price": price,
                "original_price": original_price,
                "description": description
            }
        except Exception as e:
            print(f"[WARNING] Error fetching product details from {product_url}: {e}")
            return None

    async def _scrape_root_category_page(self, url: str) -> List[str]:
        """
        Scrape a /root/ category landing page to extract sub-category and listing links.
        Returns a list of URLs to add to the queue.
        """
        discovered_urls = []

        html = await self._fetch_page(url)
        if not html:
            return discovered_urls

        soup = BeautifulSoup(html, 'lxml')
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '')
            full_url = urljoin(self.base_url, href)

            # Look for sub-category links (/root/) or listing links (/cat/)
            if '/root/' in full_url or '/cat/' in full_url:
                if full_url not in self.visited_urls:
                    discovered_urls.append(full_url)

        return discovered_urls

    async def _scrape_cat_listing_page(self, url: str, category_path: str = "") -> List[Dict]:
        """
        Scrape a /cat/ product listing page to extract all product links.
        Returns a list of product dictionaries.
        """
        products = []

        html = await self._fetch_page(url)
        if not html:
            return products

        soup = BeautifulSoup(html, 'lxml')

        # Find all product links
        all_links = soup.find_all('a', href=True)
        product_links = [link for link in all_links if '/product/' in link.get('href', '')]

        print(f"  Found {len(product_links)} product links on {url}")

        for link in product_links:
            product_url = urljoin(self.base_url, link['href'])

            # Skip if already processed or not allowed
            if product_url in self.visited_urls or not self._is_allowed_url(product_url):
                continue

            self.visited_urls.add(product_url)

            # Try to parse product card from container
            container = link.parent
            product = None

            # Try parent
            if container:
                product = self._parse_product_card(container, self.base_url)

            # Try grandparent if parent didn't work
            if not product and container and container.parent:
                product = self._parse_product_card(container.parent, self.base_url)

            # Try great-grandparent if still no product
            if not product and container and container.parent and container.parent.parent:
                product = self._parse_product_card(container.parent.parent, self.base_url)

            if product:
                product["category"] = category_path
                products.append(product)

        # Look for pagination - "Next" buttons or page numbers
        pagination_links = []
        for link in all_links:
            href = link.get('href', '').lower()
            link_text = link.get_text(strip=True).lower()

            # Look for pagination patterns
            if 'page=' in href or '/page/' in href or link_text in ['next', 'ÎµÏ€ÏŒÎ¼ÎµÎ½Î¿', 'â€º', 'Â»']:
                page_url = urljoin(self.base_url, link['href'])
                if page_url not in self.visited_urls and page_url.startswith(url.split('?')[0]):
                    pagination_links.append(page_url)

        # Process pagination pages recursively
        for page_url in pagination_links[:5]:  # Limit to 5 additional pages per listing
            if page_url not in self.visited_urls:
                self.visited_urls.add(page_url)
                page_products = await self._scrape_cat_listing_page(page_url, category_path)
                products.extend(page_products)

        return products
    
    async def scrape_products(self, preview_mode: bool = False) -> List[Dict]:
        """
        Main scraping method using sitemap-based recursive crawling.

        Args:
            preview_mode: If True, only show what would be scraped without actually scraping

        Strategy:
        1. Fetch sitemap to get all category and listing URLs
        2. Apply category filter if set
        3. Build a queue of URLs to process
        4. For /root/ URLs: extract sub-category links
        5. For /cat/ URLs: extract product links
        6. Maintain visited set to avoid duplicates
        """
        print(f"\n{'='*60}")
        print(f"Scraping {self.store_name.upper()}")
        print(f"{'='*60}\n")

        if self.category_filter:
            print(f"Category Filter: {', '.join(self.category_filter)}")

        await self._check_robots_txt()

        # Initialize browser early if not in preview mode (needed for sitemap fetch)
        if not preview_mode:
            await self.init_browser()

        all_products = []

        try:
            # Step 1: Fetch sitemap URLs
            print("Step 1: Fetching sitemap...")
            sitemap_urls = await self._fetch_sitemap_urls()

            if not sitemap_urls:
                print("[WARNING] No URLs found in sitemap, using fallback strategy")

                # Use fallback: scrape homepage to discover product links
                if not preview_mode:
                    homepage_html = await self._fetch_page(self.base_url)
                    if homepage_html:
                        soup = BeautifulSoup(homepage_html, 'lxml')
                        all_links = soup.find_all('a', href=True)

                        discovered_urls = []
                        for link in all_links:
                            href = link.get('href', '')
                            full_url = urljoin(self.base_url, href)

                            # Look for product category links and product pages
                            url_lower = full_url.lower()
                            if any(pattern in url_lower for pattern in ['/root/', '/cat/', '/category/', '/products/', '/product/']):
                                discovered_urls.append(full_url)

                            # Also look for category keywords in URLs
                            if self.category_filter:
                                for category in self.category_filter:
                                    keywords = self.category_keywords.get(category, [])
                                    for keyword in keywords:
                                        if keyword in url_lower:
                                            discovered_urls.append(full_url)

                        sitemap_urls = list(set(discovered_urls))
                        print(f"  Discovered {len(sitemap_urls)} URLs from homepage")

                        # Debug: show some discovered URLs
                        if sitemap_urls:
                            print(f"  Example discovered URLs:")
                            for url in sitemap_urls[:10]:
                                print(f"    - {url}")
                    else:
                        sitemap_urls = [self.base_url]
                else:
                    # Preview mode: just use homepage as placeholder
                    sitemap_urls = [self.base_url]
                    print(f"  Preview mode: Would discover URLs from homepage")

            # Step 2: Filter and organize URLs
            print("\nStep 2: Organizing and filtering URLs...")
            root_urls = [url for url in sitemap_urls if '/root/' in url]
            cat_urls = [url for url in sitemap_urls if '/cat/' in url]

            print(f"  Found {len(root_urls)} /root/ category pages (before filter)")
            print(f"  Found {len(cat_urls)} /cat/ listing pages (before filter)")

            # Apply category filter
            if self.category_filter:
                print(f"\n  Applying filter for keywords: {self.category_keywords}")

                # Debug: show some examples before filtering
                if root_urls:
                    print(f"  Example /root/ URLs before filter:")
                    for url in root_urls[:5]:
                        print(f"    - {url}")

                root_urls_filtered = []
                for url in root_urls:
                    if self._matches_category_filter(url):
                        root_urls_filtered.append(url)

                cat_urls_filtered = []
                for url in cat_urls:
                    if self._matches_category_filter(url):
                        cat_urls_filtered.append(url)

                # Debug: show matching URLs
                if root_urls_filtered:
                    print(f"\n  Matched /root/ URLs:")
                    for url in root_urls_filtered[:10]:
                        print(f"    - {url}")

                root_urls = root_urls_filtered
                cat_urls = cat_urls_filtered

                print(f"\n  After category filter:")
                print(f"  - {len(root_urls)} /root/ pages match")
                print(f"  - {len(cat_urls)} /cat/ pages match")

            # Step 3: Initialize queue with /root/ and /cat/ URLs
            self.category_queue = root_urls[:50]  # Start with first 50 root categories
            self.category_queue.extend(cat_urls[:100])  # Add first 100 listing pages

            print(f"\nStep 3: Processing {len(self.category_queue)} URLs from queue...")

            if preview_mode:
                print("\n[PREVIEW MODE] - Showing URLs that would be scraped:")
                for i, url in enumerate(self.category_queue[:20], 1):
                    url_type = "/root/" if "/root/" in url else "/cat/"
                    print(f"  {i}. [{url_type}] {url}")
                if len(self.category_queue) > 20:
                    print(f"  ... and {len(self.category_queue) - 20} more URLs")
                return self.category_queue  # Return URLs as "products" for preview

            # Step 4: Process queue
            processed_count = 0
            max_urls_to_process = 200  # Limit to prevent excessive scraping

            while self.category_queue and processed_count < max_urls_to_process:
                url = self.category_queue.pop(0)

                # Skip if already visited
                if url in self.visited_urls:
                    continue

                # Skip if doesn't match category filter
                if not self._matches_category_filter(url):
                    continue

                self.visited_urls.add(url)
                processed_count += 1

                print(f"\n[{processed_count}/{max_urls_to_process}] Processing: {url}")

                if '/root/' in url:
                    # Category landing page - extract sub-categories
                    print("  Type: Category Landing Page (/root/)")
                    discovered_urls = await self._scrape_root_category_page(url)
                    print(f"  Discovered {len(discovered_urls)} sub-pages")

                    # Add discovered URLs to queue (if they match filter)
                    for new_url in discovered_urls:
                        if (new_url not in self.visited_urls and
                            new_url not in self.category_queue and
                            self._matches_category_filter(new_url)):
                            self.category_queue.append(new_url)

                elif '/cat/' in url:
                    # Product listing page - extract products
                    print("  Type: Product Listing Page (/cat/)")

                    # Extract category path from URL for labeling
                    url_parts = url.split('/')
                    category_path = '/'.join([p for p in url_parts if p and p not in ['http:', 'https:', 'www.public.cy']])

                    products = await self._scrape_cat_listing_page(url, category_path)
                    print(f"  Extracted {len(products)} products")

                    # Add products to collection (avoid duplicates by URL)
                    for product in products:
                        if not any(p["url"] == product["url"] for p in all_products):
                            all_products.append(product)

                print(f"  Total products so far: {len(all_products)}")

            # Step 5: Fetch prices for products without prices
            print(f"\n\nStep 5: Fetching missing product prices...")
            products_to_update = [p for p in all_products if p.get("price", 0) == 0]
            print(f"  {len(products_to_update)} products need price information")

            max_detail_fetch = config.MAX_PRODUCT_DETAIL_FETCH
            if max_detail_fetch <= 0:
                max_detail_fetch = len(products_to_update)
            for i, product in enumerate(products_to_update[:max_detail_fetch], 1):
                print(f"  [{i}/{min(max_detail_fetch, len(products_to_update))}] Fetching price for: {product['name'][:50]}...")
                details = await self._fetch_product_details(product["url"])
                if details and details.get("price"):
                    product["price"] = details["price"]
                    if details.get("original_price"):
                        product["original_price"] = details["original_price"]
                        if product["price"] and product["original_price"]:
                            product["discount_percentage"] = ((product["original_price"] - product["price"]) / product["original_price"]) * 100
                    if details.get("description"):
                        product["description"] = details["description"]
                    print(f"      [OK] Price: {product['price']} EUR")
                else:
                    print(f"      [WARN] Could not fetch price")

            print(f"\n\n{'='*60}")
            print(f"SCRAPING COMPLETE")
            print(f"{'='*60}")
            print(f"Total URLs processed: {processed_count}")
            print(f"Total products found: {len(all_products)}")
            print(f"Products with prices: {len([p for p in all_products if p.get('price', 0) > 0])}")
            print(f"{'='*60}\n")

        finally:
            if not preview_mode:
                await self.close_browser()

        return [self.normalize_product(p) for p in all_products]

















