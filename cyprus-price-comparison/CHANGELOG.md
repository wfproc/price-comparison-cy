# Changelog

## 2026-01-26 (Part 4 - Stephanis Pagination)
- Force Stephanis category pagination to request `recordsPerPage=100` on all listing pages.
- Build page 1 URLs with pagination query params to avoid default 12-per-page results.
- Scale `max_page` based on the original `recordsPerPage` to avoid fetching unnecessary pages.

## 2026-01-26 (Part 3 - Public Scraper Fix)
- **FIX**: Public.cy scraper not fetching prices for televisions and other products.
- Issue: Public.cy uses Angular which renders content dynamically - prices weren't loaded when HTML was captured.
- Solution: Modified `_fetch_product_details()` to wait for `.product__price` selector to appear before extracting HTML.
- Added explicit 5-second wait for price element + 2 second buffer for remaining dynamic content.
- Price extraction logic verified working correctly with European format (899,00€ → 899.0).

## 2026-01-26 (Part 2 - Critical Bugfix)
- **CRITICAL BUGFIX**: Fix `find_matching_master_product()` to also check model numbers as blocking factor.
- Previous fix only updated `is_match()` but not `find_matching_master_product()`, causing A36/A56/A16 to still merge.
- Now BOTH functions enforce model blocking: products will only match to masters with the same model number.

## 2026-01-26
- Improve product matching by normalizing generic/unknown brands and extracting brands from names.
- Expand color handling to ignore "cosmic" and "cosmos" in matching.
- Ignore "5g" and "4g" tokens during matching to reduce false splits.
- Integrate webcolors library for comprehensive color detection (140+ CSS3 colors + common product colors).
- Replace hardcoded color list with dynamic color set from webcolors library.
- Fix webcolors API usage: use `webcolors.names('css3')` instead of deprecated attribute.
- Add comprehensive fallback color list (60+ colors) with better error handling.
- **MAJOR FIX**: Resolve cross-store product matching failures (iPhone 16/17 variants not matching between Public and Stephanis).
- Add color modifiers to color detection: "mist", "cosmic", "deep", "light", "sky", "space", "sage", "cloud", etc.
- Add missing colors: "ultramarine", "lavender", and other Apple product colors.
- Improve multi-word color detection (e.g., "mist blue", "cosmic orange", "space black").
- Remove store-specific descriptors from matching: "smartphone", "dual", "sim", "esim", "3g", "lte".
- Fix `normalize_text_base()` to remove stop words in addition to colors and capacity.
- **CRITICAL FIX**: Implement model number blocking to prevent false matches (e.g., Samsung A36 vs A56, iPhone 16 vs 17).
- Make model numbers a BLOCKING FACTOR: if different models detected, products cannot match regardless of other similarities.
- Add marketing terms to stop words: "awesome", "amazing", "premium", "ultimate", "special".
- Enhance model extraction patterns to handle more phone models (Samsung Z Fold/Flip, iPhone SE/Air/E, Pixel variants).
- Simplify scoring algorithm: remove model/capacity from weighted score (now checked as blocking factors).
- Add debug scripts: `debug_iphone_matching.py`, `debug_samsung_matching.py`, `test_color_fix.py`, `test_model_blocking.py` for comprehensive testing.

## 2026-01-25
- Fix search results template to use variant-aware fields (`cheapest_price`, `most_expensive`) and correct links.
- Display capacity when available and use `&euro;` for price formatting in search results.
- Force Stephanis scraper to use English site (`/en/`) for consistent category/page parsing.
