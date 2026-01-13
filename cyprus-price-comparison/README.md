# Cyprus Price Comparison Pipeline

A legal, production-grade price-comparison ingestion pipeline for Cyprus electronics retailers, similar to tweakers.nl.

## Quick Start

```bash
# Install dependencies
python setup.py

# Interactive mode - choose categories from menu
python main.py

# Or scrape specific category directly
python main.py -c smartphones

# Preview what would be scraped
python main.py -c gaming --preview
```

## Target Stores

- **Public Cyprus**: https://www.public.cy/
- **Stephanis**: https://www.stephanis.com.cy/

## Features

- ✅ **Category-based scraping** - Choose specific categories (smartphones, laptops, etc.) instead of scraping everything
- ✅ **Interactive & CLI modes** - User-friendly menu or command-line arguments for automation
- ✅ **Preview mode** - See what would be scraped before actually scraping
- ✅ **Sitemap-based crawling** - Efficient discovery of all products using sitemaps
- ✅ Legal and ethical scraping (respects robots.txt, no login required)
- ✅ Rate limiting (≤1 request/sec per domain)
- ✅ HTML caching for reproducibility
- ✅ Normalized database schema for price comparison
- ✅ Price history tracking
- ✅ Browser-like requests using Playwright

## Legal Compliance

This scraper is designed to be fully legal and ethical:

- Only crawls publicly accessible pages (no login required)
- Respects `robots.txt` files
- Does not bypass Cloudflare, Akamai, or bot checks
- Does not scrape checkout, cart, or account pages
- Uses normal browser-like requests
- Implements polite rate limiting

## Installation

### Quick Setup (Recommended)

Run the setup script which will install everything automatically:

```bash
python setup.py
```

### Manual Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

3. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

## Configuration

Edit `.env` or set environment variables:

- `DATABASE_URL`: Database connection string (default: `sqlite:///products.db`)
- `RATE_LIMIT_PER_DOMAIN`: Requests per second (default: `1.0`)
- `CACHE_DIR`: Directory for HTML cache (default: `./cache`)
- `ENABLE_CACHE`: Enable/disable HTML caching (default: `true`)
- `HEADLESS`: Run browser in headless mode (default: `true`)
- `TIMEOUT`: Page load timeout in milliseconds (default: `30000`)

## Usage

### Run the scraper:

The scraper supports multiple modes of operation:

#### **Interactive Mode** (Recommended for first-time users)

Simply run without arguments to get an interactive category selection menu:

```bash
python main.py
```

This will:
1. Show you all available categories
2. Let you choose which categories to scrape
3. Display a preview of what will be scraped
4. Run the scraper with your selections

#### **Command Line Arguments** (For automation and scripts)

```bash
# Scrape specific category
python main.py --category smartphones

# Scrape multiple categories
python main.py -c "smartphones,laptops,gaming"

# Scrape all categories (no filtering)
python main.py --all

# Preview mode - see what would be scraped without actually scraping
python main.py -c gaming --preview

# List all available categories
python main.py --list-categories

# Scrape only from Public.cy (skip Stephanis)
python main.py --public-only -c smartphones

# Scrape only from Stephanis (skip Public.cy)
python main.py --stephanis-only
```

#### **Available Categories**

- `smartphones` - Mobile phones (matches: tilefonia, kinita-smartphones)
- `laptops` - Laptops and notebooks
- `tablets` - Tablets and iPads
- `computers` - Desktop computers and peripherals (matches: computers-and-software, perifereiaka)
- `televisions` - TVs and displays (matches: tileoraseis)
- `gaming` - Gaming consoles, accessories, board games
- `audio` - Headphones, speakers, audio equipment (matches: ihos)
- `cameras` - Cameras and photography (matches: fotografia)
- `accessories` - Phone and device accessories (matches: aksesoyar, kiniton)
- `appliances` - Home appliances (matches: oikiakes-syskeyes, oikiakes-mikrosyskeyes)
- `books` - Books in Greek and English
- `stationery` - Stationery and office supplies (matches: xartika)
- `kids` - Kids toys and hobbies (matches: kids-and-toys, paidika)
- `home` - Home and personal care products

Use `python main.py --list-categories` to see the full list with matching keywords.

#### **What the scraper does:**

1. Fetches the sitemap from Public.cy
2. Filters URLs based on your category selection (if specified)
3. Recursively crawls category pages (/root/) and product listings (/cat/)
4. Extracts product information and prices
5. Saves to database and tracks price history
6. Runs product matching to group identical products across stores

### Real-World Examples:

```bash
# Example 1: Quick smartphone price check
python main.py -c smartphones --preview    # See what will be scraped
python main.py -c smartphones              # Actually scrape

# Example 2: Gaming products from Public.cy only
python main.py --public-only -c gaming

# Example 3: Multiple categories for comparison
python main.py -c "smartphones,laptops,tablets"

# Example 4: Full scrape of everything (takes longer)
python main.py --all

# Example 5: Interactive - let me choose
python main.py
# Then select from the menu:
#   1. smartphones
#   2. laptops
#   ...
#   Choose: 1
```

### Tips & Best Practices:

1. **Start with Preview Mode**: Always use `--preview` first to see what will be scraped before running the actual scrape.

2. **Use Category Filtering**: Scraping all categories takes a long time. Filter to specific categories you need:
   - ✅ Good: `python main.py -c smartphones` (fast, focused)
   - ❌ Avoid: `python main.py --all` (slow, scrapes everything)

3. **Scraping Times**:
   - Single category (smartphones): ~5-10 minutes
   - Multiple categories (smartphones,laptops,gaming): ~15-30 minutes
   - All categories: ~1-2 hours

4. **Running Regularly**: For automated price tracking, set up a cron job:
   ```bash
   # Every day at 2 AM, scrape smartphones and laptops
   0 2 * * * cd /path/to/project && python main.py -c "smartphones,laptops"
   ```

5. **Database Growth**: The database grows over time with price history. Monitor disk space if running daily scrapes.

6. **Respecting Rate Limits**: The scraper automatically respects rate limits (1 req/sec). Don't modify this without good reason.

### Query the database:

You can use the example query script:

```bash
python query_example.py
```

Or use the database functions directly:

```python
from database import get_products, get_price_comparison

# Get all products from a specific store
products = get_products(store="public")

# Get products by category
products = get_products(category="smartphones")

# Get price comparison for a product
comparison = get_price_comparison("iPhone 15", limit=10)
```

## Project Structure

```
cyprus-price-comparison/
├── main.py                 # Main orchestration script
├── setup.py               # Setup script
├── query_example.py       # Example database queries
├── config.py              # Configuration settings
├── models.py              # Database models
├── database.py            # Database operations
├── base_scraper.py        # Base scraper with common functionality
├── scrapers/
│   ├── __init__.py
│   ├── public_scraper.py  # Public Cyprus scraper
│   └── stephanis_scraper.py  # Stephanis scraper
├── cache/                 # HTML cache (created automatically)
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment file
└── README.md             # This file
```

## Database Schema

### Products Table

- `id`: Primary key
- `store`: Store identifier (e.g., "public", "stephanis")
- `store_product_id`: Product ID from the store
- `url`: Product URL
- `name`: Product name
- `description`: Product description
- `category`: Product category
- `brand`: Product brand
- `price`: Current price
- `currency`: Currency code (default: EUR)
- `original_price`: Original price (for discounted items)
- `discount_percentage`: Discount percentage
- `image_url`: Product image URL
- `availability`: Stock status
- `specifications`: JSON string of specifications
- `first_seen`: First time product was seen
- `last_updated`: Last update timestamp

### Price History Table

- `id`: Primary key
- `product_id`: Foreign key to products
- `price`: Historical price
- `currency`: Currency code
- `timestamp`: When price was recorded

## Customization

### Adding a new store:

1. Create a new scraper class in `scrapers/` that inherits from `BaseScraper`
2. Implement the `scrape_products()` method
3. Add the store to `config.py` in the `STORES` dictionary
4. Import and add the scraper to `main.py`

### Adjusting selectors:

Each scraper uses CSS selectors to find product elements. If a website's structure changes, update the selectors in the respective scraper file.

## Troubleshooting

### No products found:

- **Check category filter**: Make sure your category matches the actual URLs. Use `--preview` to see matched URLs.
- **Try a different category**: Some categories may have different URL structures. Try `--list-categories` to see all options.
- Check if the website structure has changed
- Verify that robots.txt allows crawling
- Check the cache directory for saved HTML to inspect page structure
- Run with `HEADLESS=false` to see what the browser is doing

### Few products found (expected more):

- **Increase the URL limit**: Edit `public_scraper.py` and increase `max_urls_to_process` (default: 200)
- **Check keyword matching**: Some products may not match your category keywords. Use `--all` to scrape everything.

### "Invalid category" error:

- Use `--list-categories` to see valid category names
- Category names are case-sensitive (use lowercase: `smartphones` not `Smartphones`)
- For multiple categories, use quotes: `-c "smartphones,laptops"`

### Rate limiting issues:

- Increase `RATE_LIMIT_PER_DOMAIN` if you have permission
- Check if the website has additional rate limiting

### Browser errors:

- Ensure Playwright browsers are installed: `playwright install chromium`
- Try running with `HEADLESS=false` to debug
- Check network connectivity

## License

This project is for educational and personal use. Ensure you comply with the terms of service of the websites you scrape and applicable laws in your jurisdiction.

## Disclaimer

This tool is provided as-is. Users are responsible for ensuring their use complies with:
- Website terms of service
- robots.txt directives
- Applicable laws and regulations
- Data protection regulations (GDPR, etc.)
