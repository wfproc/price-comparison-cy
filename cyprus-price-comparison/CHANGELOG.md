# Changelog

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
