"""Scraper for Stephanis (stephanis.com.cy)."""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import config


class StephanisScraper(BaseScraper):
    """Scraper for Stephanis website."""

    def __init__(self):
        super().__init__(
            store_name="stephanis",
            base_url="https://www.stephanis.com.cy/en/"
        )
        self.categories = [
            "smartphones",
            "televisions",
            "laptops",
            "gaming"
        ]
        self.category_filter: Optional[List[str]] = None
        self.category_keywords: Dict[str, List[str]] = {}

    def set_category_filter(self, categories: List[str], category_keywords: Dict[str, List[str]]):
        """
        Set category filter to limit scraping to specific categories.

        Args:
            categories: List of category names to scrape (e.g., ["smartphones", "laptops"])
            category_keywords: Dict mapping category names to URL keywords to match
        """
        self.category_filter = categories
        self.category_keywords = category_keywords
        print(f"[INFO] Stephanis category filter set: {', '.join(categories)}")

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
        text = text.replace('€', '').replace('EUR', '').replace(' ', '').strip()
        
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

    def _build_paginated_urls(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """Build a list of paginated URLs from a category page."""
        page_numbers: List[int] = []
        pagination_hrefs: List[str] = []

        for link in soup.select('a[href*="page="]'):
            href = link.get('href')
            if not href:
                continue
            match = re.search(r'page=(\d+)', href)
            if match:
                page_numbers.append(int(match.group(1)))
                pagination_hrefs.append(href)

        if not page_numbers:
            return [base_url]

        max_page = max(page_numbers)
        if max_page <= 1:
            return [base_url]

        if config.MAX_CATEGORY_PAGES > 0:
            max_page = min(max_page, config.MAX_CATEGORY_PAGES)

        # Use the first pagination link to keep existing query params like recordsPerPage/sortBy.
        sample_href = pagination_hrefs[0]
        parsed = urlparse(urljoin(base_url, sample_href))
        query = parse_qs(parsed.query)

        paged_urls = [base_url]
        for page_num in range(2, max_page + 1):
            query["page"] = [str(page_num)]
            paged_query = urlencode(query, doseq=True)
            paged = parsed._replace(query=paged_query)
            paged_urls.append(urlunparse(paged))

        return paged_urls

    def _extract_products_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract products from a listing page soup."""
        products: List[Dict] = []
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '').lower()
            if '/products/' in href and href.split('/')[-1].isdigit():
                container = link.parent
                product = None

                if container:
                    product = self._parse_product_card(container, base_url)
                if not product and container and container.parent:
                    product = self._parse_product_card(container.parent, base_url)
                if not product and container and container.parent and container.parent.parent:
                    product = self._parse_product_card(container.parent.parent, base_url)

                if product and not any(p["url"] == product["url"] for p in products):
                    products.append(product)

        return products
    
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

            # Stephanis specific: Check if this is a valid product URL (ends with number)
            if not product_url.split('/')[-1].isdigit():
                return None

            # Extract product name - Stephanis uses <li class="spotlight-list-text tile-product-name">
            name_elem = card_element.find(['li', 'h2', 'h3', 'h4'], class_=lambda x: x and ('product-name' in str(x).lower() or 'tile-product-name' in str(x).lower()))
            if not name_elem:
                name_elem = card_element.find(['h2', 'h3', 'h4', '.product-title', '.product-name'])
            if not name_elem:
                name_elem = link_elem
            name = name_elem.get_text(strip=True) if name_elem else ""

            # Extract price - Stephanis uses div class="listing-details-heading large-now-price"
            price_elem = card_element.find('div', class_=lambda x: x and ('now-price' in str(x).lower() or 'price' in str(x).lower()))
            if not price_elem:
                # Use select_one for CSS selectors
                price_elem = card_element.select_one('.price, .product-price, [class*="price"], [data-price]')
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self._extract_price(price_text)

            # Extract original price (for discounts) - use select_one for CSS selectors
            original_price_elem = card_element.select_one('.original-price, .old-price, [class*="original"], [class*="old"]')
            original_price = None
            if original_price_elem:
                original_price_text = original_price_elem.get_text(strip=True)
                original_price = self._extract_price(original_price_text)
            
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
            # Check data-productid attribute on any child element
            product_id_elem = card_element.find(attrs={'data-productid': True})
            if product_id_elem:
                product_id = product_id_elem.get('data-productid', '')
            elif 'data-product-id' in card_element.attrs:
                product_id = card_element['data-product-id']
            elif 'data-id' in card_element.attrs:
                product_id = card_element['data-id']
            else:
                # Try to extract from URL - Stephanis uses /products/.../PRODUCTID
                url_parts = product_url.split('/')
                if url_parts[-1].isdigit():
                    product_id = url_parts[-1]
            
            # Extract brand (often in name or separate element) - use select_one for CSS selectors
            brand = ""
            brand_elem = card_element.select_one('.brand, [class*="brand"]')
            if brand_elem:
                brand = brand_elem.get_text(strip=True)
            else:
                # Try to extract from name (first word often brand)
                name_parts = name.split()
                if name_parts:
                    brand = name_parts[0]

            # Availability - use select_one for CSS selectors
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
            
            if not name or not price:
                return None
            
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
            price = None
            price_selectors = [
                '.price', '.product-price', '[class*="price"]', '[data-price]',
                '[class*="Price"]', '.current-price', '.sale-price',
                '[itemprop="price"]', '.price-value'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._extract_price(price_text)
                    if price:
                        break
            
            # If still no price, search in all text
            if not price:
                page_text = soup.get_text()
                price_patterns = [
                    r'€\s*([\d,]+\.?\d*)',
                    r'([\d,]+\.?\d*)\s*€',
                    r'EUR\s*([\d,]+\.?\d*)',
                    r'([\d,]+\.?\d*)\s*EUR',
                    r'price["\']?\s*[:=]\s*([\d,]+\.?\d*)',
                ]
                for pattern in price_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        price = self._extract_price(match.group(1))
                        if price and price > 0:  # Valid price
                            break
            
            # Extract description
            description = ""
            desc_selectors = ['.description', '.product-description', '[class*="description"]', '[itemprop="description"]']
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)[:1000]  # Limit length
                    break
            
            # Extract original price for discounts
            original_price = None
            original_price_elem = soup.select_one('.original-price, .old-price, [class*="original-price"], [class*="old-price"]')
            if original_price_elem:
                original_price_text = original_price_elem.get_text(strip=True)
                original_price = self._extract_price(original_price_text)
            
            return {
                "price": price,
                "original_price": original_price,
                "description": description
            }
        except Exception as e:
            print(f"[WARNING] Error fetching product details from {product_url}: {e}")
            return None
    
    async def _scrape_category(self, category: str) -> List[Dict]:
        """Scrape products from a category page."""
        products = []
        
        # Try common category URL patterns
        category_urls = [
            urljoin(self.base_url, f"/{category}"),
            urljoin(self.base_url, f"/category/{category}"),
            urljoin(self.base_url, f"/products/{category}"),
            urljoin(self.base_url, f"/shop/{category}"),
            urljoin(self.base_url, f"/en/{category}"),  # English language prefix
        ]
        
        for category_url in category_urls:
            html = await self._fetch_page(category_url)
            if html:
                soup = BeautifulSoup(html, 'lxml')

                paged_urls = self._build_paginated_urls(category_url, soup)
                print(f"  Found {len(paged_urls)} page(s) for category listing")

                for page_url in paged_urls:
                    print(f"  Fetching page: {page_url}")
                    page_html = html if page_url == category_url else await self._fetch_page(page_url)
                    if not page_html:
                        continue
                    page_soup = BeautifulSoup(page_html, 'lxml')
                    page_products = self._extract_products_from_soup(page_soup, self.base_url)
                    for product in page_products:
                        product["category"] = category
                        if not any(p["url"] == product["url"] for p in products):
                            products.append(product)
                
                if products:
                    break  # Found products, no need to try other URLs
        
        return products
    
    async def scrape_products(self, preview_mode: bool = False) -> List[Dict]:
        """
        Main scraping method.

        Args:
            preview_mode: If True, only show what would be scraped without actually scraping
        """
        print(f"\n{'='*60}")
        print(f"Scraping {self.store_name.upper()}")
        print(f"{'='*60}\n")

        if self.category_filter:
            print(f"Category Filter: {', '.join(self.category_filter)}")

        if preview_mode:
            print("[PREVIEW MODE] - Stephanis scraper would run normally")
            if self.category_filter:
                print(f"Would filter for: {', '.join(self.category_filter)}")
            return []

        await self._check_robots_txt()
        await self.init_browser()
        
        all_products = []
        
        try:
            # First, scrape main page thoroughly (but only if no category filter is set)
            # When category filter is active, we only scrape from category pages
            if not self.category_filter:
                print("Scraping main page...")
                html = await self._fetch_page(self.base_url, use_cache=False)
                if html:
                    soup = BeautifulSoup(html, 'lxml')
                    # Find product links on main page
                    # Stephanis uses /el/products/category/.../PRODUCTID pattern
                    all_links = soup.find_all('a', href=True)
                    product_links = []
                    for link in all_links:
                        href = link.get('href', '').lower()
                        # Stephanis products: /el/products/.../NUMBER or /products/.../NUMBER
                        if '/products/' in href and href.split('/')[-1].isdigit():
                            product_links.append(link)

                    print(f"  Found {len(product_links)} product links on main page")

                    for link in product_links:
                        container = link.parent
                        product = None

                        # Try multiple container levels
                        if container:
                            product = self._parse_product_card(container, self.base_url)
                        if not product and container and container.parent:
                            product = self._parse_product_card(container.parent, self.base_url)
                        if not product and container and container.parent and container.parent.parent:
                            product = self._parse_product_card(container.parent.parent, self.base_url)

                        if product and not any(p["url"] == product["url"] for p in all_products):
                            all_products.append(product)
            else:
                print("Skipping main page scraping (category filter active)")
                html = await self._fetch_page(self.base_url, use_cache=False)
                if html:
                    soup = BeautifulSoup(html, 'lxml')
                    all_links = soup.find_all('a', href=True)
                else:
                    all_links = []

            # Look for category links - Stephanis uses /el/products/CATEGORY/ pattern
            if html:
                print("  Looking for category links...")
                category_links = []
                for link in all_links:
                    href = link.get('href', '').lower()
                    # Look for category pages (not product pages - those end with numbers)
                    if '/products/' in href and not href.split('/')[-1].isdigit():
                        if any(cat in href for cat in ['information-technology', 'telecommunications', 'laptops', 'smartphones', 'televisions', 'gaming', 'tablets', 'phones', 'computers', 'mobile']):
                            full_url = urljoin(self.base_url, link.get('href', ''))
                            if full_url.startswith('http') and self._matches_category_filter(full_url):
                                category_links.append(full_url)

                category_links = list(set(category_links))[:10]
                print(f"  Found {len(category_links)} category pages to scrape (after filter)")

                for cat_url in category_links:
                    cat_html = await self._fetch_page(cat_url)
                    if cat_html:
                        cat_soup = BeautifulSoup(cat_html, 'lxml')
                        paged_urls = self._build_paginated_urls(cat_url, cat_soup)
                        print(f"    Found {len(paged_urls)} page(s) in {cat_url}")

                        for page_url in paged_urls:
                            print(f"    Fetching page: {page_url}")
                            page_html = cat_html if page_url == cat_url else await self._fetch_page(page_url)
                            if not page_html:
                                continue
                            page_soup = BeautifulSoup(page_html, 'lxml')
                            page_products = self._extract_products_from_soup(page_soup, self.base_url)
                            for product in page_products:
                                if product and not any(p["url"] == product["url"] for p in all_products):
                                    all_products.append(product)
            
            # Try scraping by category (only if no category filter, or category matches filter)
            for category in self.categories:
                # Skip if category filter is set and this category doesn't match
                if self.category_filter and category not in self.category_filter:
                    continue

                print(f"Scraping category: {category}")
                category_products = await self._scrape_category(category)
                for product in category_products:
                    if not any(p["url"] == product["url"] for p in all_products):
                        all_products.append(product)
                print(f"  Found {len(category_products)} products\n")
            
            # Fetch prices from product pages for products without prices
            print(f"\nFetching prices from product pages...")
            products_to_update = [p for p in all_products if p.get("price", 0) == 0]
            print(f"  {len(products_to_update)} products need price information")
            
            for product in products_to_update:
                details = await self._fetch_product_details(product["url"])
                if details and details.get("price"):
                    product["price"] = details["price"]
                    if details.get("original_price"):
                        product["original_price"] = details["original_price"]
                        if product["price"] and product["original_price"]:
                            product["discount_percentage"] = ((product["original_price"] - product["price"]) / product["original_price"]) * 100
                    if details.get("description"):
                        product["description"] = details["description"]
                    print(f"  [OK] Found price for: {product['name'][:50]} - {product['price']} EUR")
            
            print(f"\n[OK] Total products found: {len(all_products)}")
            
        finally:
            await self.close_browser()
        
        return [self.normalize_product(p) for p in all_products]
