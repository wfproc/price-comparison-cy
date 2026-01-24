# Changelog

All notable changes to the Cyprus Price Comparison project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2026-01-23
- **Stephanis Main Page Skipping** - When category filter is active, Stephanis scraper now skips main page product scraping
  - Prevents scraping unrelated products (costumes, general merchandise) from homepage
  - Only scrapes category-specific pages when filter is set
  - Fixed in `stephanis_scraper.py` lines 395-436
- **Improved Stephanis Category Keywords** - More precise URL matching for smartphones and laptops categories
  - Smartphones: Changed from generic "mobile-phone" to specific "smartphones-and-feature-phones/smartphones"
  - Laptops: Changed from generic "laptop/notebook" to specific "laptops-and-accessories/laptops"
  - Now uses path-based matching to exclude accessories, cables, and other related categories
  - Fixed in `main.py` lines 50-51

### Added - 2026-01-22
- **Product Variants System** - New `MasterProductVariant` table to handle storage capacity variants (128GB, 256GB, etc.)
  - Products now link to both `master_product_id` and `variant_id`
  - Automatic variant creation during product matching
  - Variant-aware search functionality
- **Enhanced Product Matching** - Smart base normalization that ignores capacity/color
  - `normalize_text_base()` - removes capacity and color tokens for master matching
  - `extract_base_tokens()` - extracts tokens for base product matching
  - `build_base_name()` - creates clean display names without variants
  - `get_or_create_variant()` - manages variant lifecycle
- **Configuration Limits**
  - `MAX_PRODUCT_DETAIL_FETCH` - controls number of product detail fetches (default: unlimited)
  - `MAX_CATEGORY_PAGES` - controls category scraping depth (default: unlimited)
- **Stephanis-Specific Category Keywords** - Separate URL keywords for Stephanis scraper
  - `PUBLIC_CATEGORY_KEYWORDS` - Public.cy specific keywords
  - `STEPHANIS_CATEGORY_KEYWORDS` - Stephanis specific keywords (telecommunications, information-technology patterns)
- **Database Migration Support** - Auto-detection and migration for `variant_id` column

### Fixed - 2026-01-23
- **Stephanis Laptops Category Filtering** - Fixed scraper including laptop accessories
  - Issue: When filtering for "laptops", scraper found 1,249 products including USB chargers, laptop cases, cooling pads, and power supplies
  - Root cause: Keywords "laptop" and "notebook" matched parent category "laptops-and-accessories" which contains both actual laptops AND accessory subcategories
  - Solution: Use specific path patterns "laptops-and-accessories/laptops" and "last-pieces-information-technology/laptops"
  - Impact: Now only scrapes actual laptop products, excludes all accessories
- **Stephanis Smartphones Category Filtering** - Fixed scraper scraping unrelated products
  - Issue: When filtering for "smartphones", scraper was finding costumes, gaming items, and accessories
  - Root cause: Main page contained featured products from all categories
  - Solution: Skip main page scraping when category filter is active, only use category pages
  - Result: Reduced products from 1787 to 597 (eliminated irrelevant products)
  - Impact: Stephanis now correctly scrapes only smartphones and feature phones
- **Stephanis Keyword Overmatch** - Fixed keywords matching mobile-phone-accessories
  - Issue: Keyword "mobile-phone" matched both "/mobile-phones/" and "/mobile-phone-accessories/"
  - Solution: Use full path patterns like "smartphones-and-feature-phones/smartphones"
  - Result: No longer scrapes earphones, cables, power banks, or other accessories
  - Impact: Clean smartphone-only results

### Fixed - 2026-01-22
- **BeautifulSoup CSS Selector Bug** - Changed `.find()` to `.select_one()` for CSS selectors
  - Fixed in `public_scraper.py` line 259, 270
  - Fixed in `stephanis_scraper.py` lines 119, 125, 160, 171
  - Impact: Price, brand, and availability extraction now works correctly
- **Stephanis Category Filter Bypass** - Added category filter check in self.categories loop
  - Fixed in `stephanis_scraper.py` line 417
  - Impact: Stephanis now respects user's category selection, no longer scrapes unwanted categories
- **ProductMatcher Session Leak** - Added `matcher.close()` in finally blocks
  - Fixed in `search_products.py` line 162
  - Impact: Prevents database connection exhaustion
- **Flask Security Issues**
  - Changed `debug=True` to environment variable (default: False)
  - Changed `host='0.0.0.0'` to `127.0.0.1` by default (use `FLASK_HOST` to override)
  - Added security warnings when unsafe settings detected
  - Fixed in `app.py` lines 303-314
- **Public.cy Anti-Bot Detection** - Enhanced browser fingerprinting
  - Switched to Firefox browser (better bot detection bypass)
  - Added comprehensive anti-detection measures (stealth scripts, realistic headers)
  - Runs in headless mode by default
  - Added browser-based sitemap fetching as fallback
- **Config Import Error** - Added `import config` to `public_scraper.py` line 10

### Changed - 2026-01-22
- **Database Schema** - Enhanced with foreign key constraints and relationships
  - `Product.master_product_id` → ForeignKey with `SET NULL` on delete
  - `Product.variant_id` → ForeignKey with `SET NULL` on delete
  - `PriceHistory.product_id` → ForeignKey with `CASCADE` on delete
  - Added bidirectional SQLAlchemy relationships for ORM navigation
- **Search Functionality** - Now variant-aware with capacity filtering
  - `search_products()` can filter by storage capacity in queries
  - Returns separate results for each variant with proper pricing
  - Added `get_product_by_variant_id()` function
- **Product Matching Algorithm** - Separates base products from variants
  - Uses base normalization for master product matching
  - Creates variants automatically based on extracted capacity
  - Better handling of products with multiple storage options

## Project Structure

```
MasterProduct (Base Product)
  ├─ MasterProductVariant (128GB)
  │   └─ Product (Store Listing)
  ├─ MasterProductVariant (256GB)
  │   └─ Product (Store Listing)
```

## Migration Notes

### From Previous Versions
If you have an existing database:
1. The `variant_id` column will be automatically added to the `products` table
2. Run product matching to populate variant assignments: `python product_matcher.py --rematch`
3. Foreign key constraints are enforced on new installations only (SQLite limitation)

## Developer Notes
- All our bug fixes from the code review have been applied
- Product variant system integrated from other developer's work
- Session leak fix re-applied after merge
- All scrapers now use correct CSS selector methods
