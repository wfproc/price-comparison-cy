"""Scraper for Stephanis (stephanis.com.cy)."""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from urllib.parse import urljoin, urlparse


class StephanisScraper(BaseScraper):
    """Scraper for Stephanis website."""
    
    def __init__(self):
        super().__init__(
            store_name="stephanis",
            base_url="https://www.stephanis.com.cy/"
        )
        self.categories = [
            "smartphones",
            "televisions",
            "laptops",
            "gaming"
        ]
    
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
                price_elem = card_element.find(['.price', '.product-price', '[class*="price"]', '[data-price]'])
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self._extract_price(price_text)
            
            # Extract original price (for discounts)
            original_price_elem = card_element.find(['.original-price', '.old-price', '[class*="original"]', '[class*="old"]'])
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
            availability_elem = card_element.find(['.availability', '.stock', '[class*="stock"]', '[class*="available"]'])
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
            urljoin(self.base_url, f"/el/{category}"),  # Greek language prefix
        ]
        
        for category_url in category_urls:
            html = await self._fetch_page(category_url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                
                # Find product links - Stephanis uses /el/products/category/.../PRODUCTID pattern
                # Look for links that end with a number (product ID)
                all_links = soup.find_all('a', href=True)
                product_links = []
                for link in all_links:
                    href = link.get('href', '').lower()
                    # Stephanis products: /el/products/.../NUMBER or /products/.../NUMBER
                    if '/products/' in href and href.split('/')[-1].isdigit():
                        product_links.append(link)
                
                # For each product link, get its container
                for link in product_links:
                    container = link.parent
                    if container is None:
                        continue
                    
                    # If parent is just a wrapper, try grandparent
                    if container.name in ['div', 'span'] and len(container.get('class', [])) == 0:
                        container = container.parent
                    
                    product = self._parse_product_card(container, self.base_url)
                    if product:
                        product["category"] = category
                        # Avoid duplicates
                        if not any(p["url"] == product["url"] for p in products):
                            products.append(product)
                
                if products:
                    break  # Found products, no need to try other URLs
        
        return products
    
    async def scrape_products(self) -> List[Dict]:
        """Main scraping method."""
        print(f"\n{'='*60}")
        print(f"Scraping {self.store_name.upper()}")
        print(f"{'='*60}\n")
        
        await self._check_robots_txt()
        await self.init_browser()
        
        all_products = []
        
        try:
            # First, scrape main page thoroughly
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
                
                # Look for category links - Stephanis uses /el/products/CATEGORY/ pattern
                print("  Looking for category links...")
                category_links = []
                for link in all_links:
                    href = link.get('href', '').lower()
                    # Look for category pages (not product pages - those end with numbers)
                    if '/products/' in href and not href.split('/')[-1].isdigit():
                        if any(cat in href for cat in ['information-technology', 'telecommunications', 'laptops', 'smartphones', 'televisions', 'gaming', 'tablets', 'phones', 'computers']):
                            full_url = urljoin(self.base_url, link.get('href', ''))
                            if full_url.startswith('http'):
                                category_links.append(full_url)
                
                category_links = list(set(category_links))[:10]
                print(f"  Found {len(category_links)} category pages to scrape")
                
                for cat_url in category_links:
                    cat_html = await self._fetch_page(cat_url)
                    if cat_html:
                        cat_soup = BeautifulSoup(cat_html, 'lxml')
                        cat_links = cat_soup.find_all('a', href=True)
                        # Find product links in category (end with number)
                        cat_product_links = []
                        for l in cat_links:
                            href = l.get('href', '').lower()
                            if '/products/' in href and href.split('/')[-1].isdigit():
                                cat_product_links.append(l)

                        print(f"    Found {len(cat_product_links)} products in {cat_url.split('/')[-2] if cat_url.split('/')[-1] == '' else cat_url.split('/')[-1]}")

                        for link in cat_product_links:
                            container = link.parent
                            if container:
                                product = self._parse_product_card(container, self.base_url)
                                if product and not any(p["url"] == product["url"] for p in all_products):
                                    all_products.append(product)
            
            # Try scraping by category
            for category in self.categories:
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
