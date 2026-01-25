"""Main orchestration script for the price comparison pipeline."""
import asyncio
import sys
import os
import argparse
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


# Category keywords for Public.cy (based on actual sitemap analysis)
# These keywords match the actual URL paths in Public.cy's sitemap
PUBLIC_CATEGORY_KEYWORDS = {
    "smartphones": ["tilefonia", "kinita-smartphones"],  # /root/tilefonia
    "laptops": ["laptop", "notebooks", "portable-computers"],
    "tablets": ["tablet", "ipad"],
    "computers": ["computers-and-software", "perifereiaka", "desktop"],  # /root/computers-and-software
    "televisions": ["tileoraseis", "tv"],  # tileoraseis = TVs in Greek
    "gaming": ["gaming", "playstation", "xbox", "nintendo", "board-games"],  # /gaming/
    "audio": ["ihos", "audio", "headphones", "speakers"],  # ihos = audio/sound in Greek
    "cameras": ["fotografia", "camera", "photo", "fotografikes"],  # fotografia = photography
    "accessories": ["aksesoyar", "kiniton"],  # aksesoyar = accessories, kiniton = mobile accessories
    "appliances": ["oikiakes-syskeyes", "oikiakes-mikrosyskeyes", "thermansi-klimatismos"],  # household appliances
    "books": ["books", "greek-books", "english"],  # /books/
    "stationery": ["xartika"],  # xartika = stationery
    "kids": ["kids-and-toys", "paidika", "hobbies"],  # toys and kids items
    "home": ["home", "prosopiki-frontida-and-omorfia"],  # home and personal care
}

# Category keywords for Stephanis (based on their URL structure)
# Stephanis uses /en/products/{category}/{subcategory}/ pattern
STEPHANIS_CATEGORY_KEYWORDS = {
    "smartphones": ["smartphones-and-feature-phones", "telecommunications/mobile-phones", "mobile-phone", "smartphone"],
    "laptops": ["laptops-and-accessories", "information-technology/laptops", "laptop", "notebook"],
    "tablets": ["tablets-and-ereaders", "information-technology/tablets", "tablet", "ipad"],
    "computers": ["information-technology/computers", "desktop", "pc"],
    "televisions": ["image-and-sound/televisions", "tv", "television"],
    "gaming": ["gaming/gaming-consoles", "gaming/", "playstation", "xbox", "nintendo"],
    "audio": ["image-and-sound/sound", "audio", "headphones", "speakers"],
    "cameras": ["image-and-sound/photography", "camera", "photo"],
    "accessories": ["telecommunications/mobile-phone-accessories", "accessory", "accessories"],
    "appliances": ["home-appliances", "appliances"],
}


def get_available_categories():
    """Return list of available category names."""
    return sorted(PUBLIC_CATEGORY_KEYWORDS.keys())


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Cyprus Price Comparison Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Interactive mode - choose categories
  python main.py --all                     # Scrape all categories
  python main.py --category smartphones    # Scrape only smartphones
  python main.py -c "smartphones,laptops"  # Scrape multiple categories
  python main.py -c gaming --preview       # Preview what would be scraped
  python main.py --public-only             # Only scrape Public.cy
  python main.py --stephanis-only          # Only scrape Stephanis
        """
    )

    parser.add_argument(
        "-c", "--category",
        type=str,
        help="Category to scrape (comma-separated for multiple). Available: " + ", ".join(get_available_categories())
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Scrape all categories (no filtering)"
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview mode - show what would be scraped without actually scraping"
    )

    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available categories and exit"
    )

    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Only scrape Public.cy (skip Stephanis)"
    )

    parser.add_argument(
        "--stephanis-only",
        action="store_true",
        help="Only scrape Stephanis (skip Public.cy)"
    )

    return parser.parse_args()


def interactive_store_selection():
    """Interactive prompt for store selection."""
    print("\n" + "="*60)
    print("STORE SELECTION")
    print("="*60)
    print("\nAvailable stores:")
    print("   1. Public.cy")
    print("   2. Stephanis")
    print("   3. All stores")
    print("   0. Exit")

    while True:
        try:
            choice = input("\nEnter your choice (number or name): ").strip().lower()

            if choice in ["0", "exit"]:
                print("Exiting...")
                sys.exit(0)

            if choice in ["1", "public", "public.cy"]:
                return True, False

            if choice in ["2", "stephanis"]:
                return False, True

            if choice in ["3", "all"]:
                return True, True

            print("Invalid choice. Please try again.")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)


def interactive_category_selection():
    """Interactive prompt for category selection."""
    print("\n" + "="*60)
    print("CATEGORY SELECTION")
    print("="*60)
    print("\nAvailable categories:")

    categories = get_available_categories()
    for i, cat in enumerate(categories, 1):
        keywords = ", ".join(PUBLIC_CATEGORY_KEYWORDS.get(cat, STEPHANIS_CATEGORY_KEYWORDS.get(cat, [])))
        print(f"  {i:2}. {cat.capitalize():15} (matches: {keywords})")

    print(f"\n  {len(categories)+1:2}. All categories")
    print("   0. Exit")

    while True:
        try:
            choice = input("\nEnter your choice (number or category name): ").strip().lower()

            # Check if exit
            if choice == "0" or choice == "exit":
                print("Exiting...")
                sys.exit(0)

            # Check if all
            if choice == str(len(categories)+1) or choice == "all":
                return None  # None means all categories

            # Check if number
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(categories):
                    return [categories[choice_num - 1]]
            except ValueError:
                pass

            # Check if category name
            if choice in categories:
                return [choice]

            # Check if comma-separated list
            if "," in choice:
                selected = [c.strip() for c in choice.split(",")]
                valid = [c for c in selected if c in categories]
                if valid:
                    return valid
                else:
                    print(f"Invalid categories. Please choose from: {', '.join(categories)}")
                    continue

            print("Invalid choice. Please try again.")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)


async def run_scrapers(categories=None, preview_mode=False, scrape_public=True, scrape_stephanis=True):
    """
    Run all scrapers and save results to database.

    Args:
        categories: List of category names to scrape, or None for all
        preview_mode: If True, only show what would be scraped without scraping
        scrape_public: Whether to scrape Public.cy
        scrape_stephanis: Whether to scrape Stephanis
    """
    print("="*60)
    print("CYPRUS PRICE COMPARISON PIPELINE")
    print("="*60)
    print(f"Database: {config.DATABASE_URL}")
    print(f"Rate Limit: {config.RATE_LIMIT_PER_DOMAIN} req/sec")
    print(f"Cache: {'Enabled' if config.ENABLE_CACHE else 'Disabled'}")

    if categories:
        category_names = ", ".join(categories)
        print(f"Categories: {category_names}")
    else:
        print(f"Categories: All")

    if preview_mode:
        print(f"Mode: PREVIEW ONLY (no actual scraping)")

    print("="*60)
    print()

    # Check if Playwright browsers are installed (skip in preview mode)
    if not preview_mode:
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

    # Initialize database (skip in preview mode)
    if not preview_mode:
        print("Initializing database...")
        init_db()
        print()

    # Initialize scrapers based on flags
    scrapers = []
    if scrape_public:
        public_scraper = PublicScraper()
        # Pass category filters to Public scraper with Public-specific keywords
        if categories:
            public_scraper.set_category_filter(categories, PUBLIC_CATEGORY_KEYWORDS)
        scrapers.append(public_scraper)

    if scrape_stephanis:
        stephanis_scraper = StephanisScraper()
        # Pass category filters to Stephanis scraper with Stephanis-specific keywords
        if categories:
            stephanis_scraper.set_category_filter(categories, STEPHANIS_CATEGORY_KEYWORDS)
        scrapers.append(stephanis_scraper)

    if not scrapers:
        print("[ERROR] No scrapers selected! Use --public-only or --stephanis-only")
        return

    all_products = []

    # Run scrapers sequentially (to respect rate limits)
    for scraper in scrapers:
        try:
            products = await scraper.scrape_products(preview_mode=preview_mode)
            all_products.extend(products)

            if preview_mode:
                print(f"\n[PREVIEW] {scraper.store_name}: Would scrape ~{len(products)} URLs")
            else:
                print(f"[OK] {scraper.store_name}: {len(products)} products scraped\n")
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"[ERROR] Error scraping {scraper.store_name}: {error_msg}\n")
            import traceback
            try:
                traceback.print_exc()
            except UnicodeEncodeError:
                print("[ERROR] (Traceback contains non-ASCII characters)")

    if preview_mode:
        print("\n" + "="*60)
        print("PREVIEW COMPLETE - No data was scraped")
        print("="*60)
        print(f"Total URLs that would be scraped: {len(all_products)}")
        print("\nTo actually scrape, run without --preview flag")
        return
    
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
        # Parse command line arguments
        args = parse_arguments()

        # Handle --list-categories
        if args.list_categories:
            print("\nAvailable categories:")
            for cat in get_available_categories():
                keywords = ", ".join(PUBLIC_CATEGORY_KEYWORDS.get(cat, STEPHANIS_CATEGORY_KEYWORDS.get(cat, [])))
                print(f"  - {cat.capitalize():15} (matches: {keywords})")
            sys.exit(0)

        # Determine which stores to scrape
        scrape_public = not args.stephanis_only
        scrape_stephanis = not args.public_only
        if not args.public_only and not args.stephanis_only and not args.category and not args.all:
            scrape_public, scrape_stephanis = interactive_store_selection()

        # Determine categories to scrape
        categories = None

        if args.all:
            # Explicit --all flag: scrape everything
            categories = None
        elif args.category:
            # CLI argument provided
            category_list = [c.strip() for c in args.category.split(",")]
            valid_categories = get_available_categories()

            # Validate categories
            invalid = [c for c in category_list if c not in valid_categories]
            if invalid:
                print(f"[ERROR] Invalid categories: {', '.join(invalid)}")
                print(f"Available categories: {', '.join(valid_categories)}")
                sys.exit(1)

            categories = category_list
        else:
            # No CLI argument: use interactive mode
            categories = interactive_category_selection()

        # Run scrapers
        asyncio.run(run_scrapers(
            categories=categories,
            preview_mode=args.preview,
            scrape_public=scrape_public,
            scrape_stephanis=scrape_stephanis
        ))

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
