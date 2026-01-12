# Cyprus Price Comparison Pipeline

A legal, production-grade price-comparison ingestion pipeline for Cyprus electronics retailers, similar to tweakers.nl.

## Target Stores

- **Public Cyprus**: https://www.public.cy/
- **Stephanis**: https://www.stephanis.com.cy/

## Features

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

```bash
python main.py
```

This will:
1. Check robots.txt for each store
2. Scrape product data from all configured stores
3. Normalize and save products to the database
4. Track price history

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

- Check if the website structure has changed
- Verify that robots.txt allows crawling
- Check the cache directory for saved HTML to inspect page structure
- Run with `HEADLESS=false` to see what the browser is doing

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
