"""Main orchestration script for the price comparison pipeline."""
import asyncio
import sys
import os
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding for Windows console
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # Fall back to default encoding if reconfiguration fails

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers import PublicScraper, StephanisScraper
from database import save_products, init_db
from models import get_session, Product, MasterProduct
from product_matcher import run_product_matching
import config


async def run_scrapers():
    """Run all scrapers and save results to database."""
    print("="*60)
    print("CYPRUS PRICE COMPARISON PIPELINE")
    print("="*60)
    print(f"Database: {config.DATABASE_URL}")
    print(f"Rate Limit: {config.RATE_LIMIT_PER_DOMAIN} req/sec")
    print(f"Cache: {'Enabled' if config.ENABLE_CACHE else 'Disabled'}")
    print("="*60)
    print()
    
    # Check if Playwright browsers are installed
    try:
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        await browser.close()
        await playwright.stop()
    except Exception as e:
        print("[ERROR] Playwright browsers are not installed!")
        print("Please run the following command to install them:")
        print("  python -m playwright install chromium")
        print()
        print("Or run the setup script:")
        print("  python setup.py")
        return
    
    # Initialize database
    print("Initializing database...")
    init_db()
    print()
    
    # Initialize scrapers
    scrapers = [
        PublicScraper(),
        StephanisScraper(),
    ]
    
    all_products = []
    
    # Run scrapers sequentially (to respect rate limits)
    for scraper in scrapers:
        try:
            products = await scraper.scrape_products()
            all_products.extend(products)
            print(f"[OK] {scraper.store_name}: {len(products)} products scraped\n")
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"[ERROR] Error scraping {scraper.store_name}: {error_msg}\n")
            import traceback
            try:
                traceback.print_exc()
            except UnicodeEncodeError:
                print("[ERROR] (Traceback contains non-ASCII characters)")
    
    # Save to database
    if all_products:
        print("="*60)
        print("Saving products to database...")
        created, updated = save_products(all_products)
        print(f"[OK] Created: {created} products")
        print(f"[OK] Updated: {updated} products")
        print(f"[OK] Total processed: {len(all_products)} products")
        print("="*60)
    else:
        print("[WARNING] No products found to save.")
    
    # Run product matching to group products across stores
    print("\n")
    print("="*60)
    print("RUNNING PRODUCT MATCHING")
    print("="*60)
    matching_stats = run_product_matching(rematch=False)

    # Print summary
    session = get_session()
    try:
        total_products = session.query(Product).count()
        total_masters = session.query(MasterProduct).count()
        stores = session.query(Product.store).distinct().all()
        matched_products = session.query(Product).filter(Product.master_product_id.isnot(None)).count()

        print(f"\nDatabase Summary:")
        print(f"  Total products: {total_products}")
        print(f"  Matched products: {matched_products}")
        print(f"  Master products: {total_masters}")
        print(f"  Stores: {', '.join([s[0] for s in stores])}")
        print(f"  Average products per master: {total_products / total_masters:.1f}" if total_masters > 0 else "")
    finally:
        session.close()


if __name__ == "__main__":
    try:
        asyncio.run(run_scrapers())
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\n[ERROR] Fatal error: {error_msg}")
        import traceback
        try:
            traceback.print_exc()
        except UnicodeEncodeError:
            print("[ERROR] (Traceback contains non-ASCII characters)")
        sys.exit(1)
