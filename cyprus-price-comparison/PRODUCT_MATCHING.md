# Product Matching System

## Overview

The product matching system groups the same product across different stores, even when stores name them differently. This creates a **single source of truth** for each unique product, making it easy to compare prices across stores.

## Example

**Store 1 (Public.cy):**
```
Smartphone APPLE iPhone 16 Pro 128GB Dual SIM black titanium
Price: €1,299.00
```

**Store 2 (Stephanis):**
```
Apple iPhone 16 Pro 128GB - Black Titanium
Price: €1,349.00
```

Both of these are **matched to the same master product**, allowing users to:
- Search for "iphone 16 pro 128gb" and get both results
- See the price difference (€50 in this case)
- Choose the cheapest option

---

## Architecture

### Database Schema

#### `master_products` Table
Single source of truth for each unique product:
- `id` - Unique master product ID
- `canonical_name` - Standardized product name
- `brand` - Extracted brand (e.g., "apple", "samsung")
- `model` - Extracted model (e.g., "iphone 16 pro", "galaxy s24")
- `category` - Product category
- `normalized_name` - Lowercase, no special chars (for searching)
- `search_tokens` - Space-separated tokens for fuzzy matching

#### `products` Table
Individual store listings:
- All existing fields (store, name, price, URL, etc.)
- **NEW:** `master_product_id` - Foreign key linking to master product

### Matching Algorithm

The system uses **multi-strategy fuzzy matching** with weighted scoring:

1. **Brand Matching** (gate check)
   - Extracts brand from product name
   - Products with different brands are NOT matched
   - Recognizes 30+ major brands (Apple, Samsung, Xiaomi, etc.)

2. **Name Similarity** (40% weight)
   - Uses SequenceMatcher for fuzzy string comparison
   - Handles typos and variations

3. **Token Overlap** (40% weight)
   - Extracts meaningful tokens (removes stop words like "smartphone", "dual sim")
   - Calculates Jaccard similarity between token sets
   - Example: ["apple", "iphone", "16", "pro", "128gb"] vs ["apple", "iphone", "16", "pro", "128gb", "black"]

4. **Capacity Matching** (10% weight)
   - Extracts storage capacity (128gb, 256gb, 1tb)
   - Ensures products with different storage aren't matched

5. **Model Matching** (10% weight)
   - Extracts model identifier using regex patterns
   - Handles common patterns: "iPhone 16 Pro", "Galaxy S24 Ultra", "Pixel 8"

**Threshold:** Products are matched if combined score ≥ 0.70 (70%)

---

## Usage

### 1. Run Product Matching

After scraping, the matching runs automatically in `main.py`:

```bash
python main.py
```

Or run matching separately on existing data:

```bash
# Match new products only
python product_matcher.py

# Re-match all products from scratch (rebuilds master products)
python product_matcher.py --rematch
```

### 2. Search for Products

Search across all stores:

```bash
python search_products.py "iphone 16 pro 128gb"
```

Output:
```
================================================================================
PRICE COMPARISON: iphone 16 pro 128gb
================================================================================

1. Apple iPhone 16 Pro 128GB Black Titanium
   Brand: apple
   Model: iphone 16 pro

   Found in 2 store(s):
   Cheapest: €1,299.00
   Most expensive: €1,349.00
   SAVE EUR50.00 (3.7%) by choosing cheapest!

   Store prices:
     • PUBLIC        €1,299.00
       https://www.public.cy/product/.../iphone-16-pro-128gb/12345
     • STEPHANIS     €1,349.00
       https://www.stephanis.com.cy/el/products/.../67890
```

### 3. Programmatic Access

```python
from search_products import search_products

# Search for products
results = search_products("ipad pro 256gb", limit=10)

for product in results:
    print(f"{product['name']}")
    print(f"  Cheapest: €{product['cheapest_price']:.2f}")
    print(f"  Stores: {product['store_count']}")

    for store in product['stores']:
        print(f"    - {store['store']}: €{store['price']:.2f}")
```

### 4. Get Product by Master ID

```python
from search_products import get_product_by_master_id

product = get_product_by_master_id(42)
print(f"{product['name']} available in {len(product['stores'])} stores")
```

---

## How Matching Works (Step-by-Step)

### Step 1: Normalization

Input: `"Smartphone APPLE iPhone 16 Pro 128GB Dual SIM - black titanium"`

1. Convert to lowercase
2. Normalize units: "128 GB" → "128gb"
3. Remove special characters
4. Extract tokens: ["apple", "iphone", "16", "pro", "128gb", "black", "titanium"]
5. Remove stop words: ["apple", "iphone", "16", "pro", "128gb"]

### Step 2: Feature Extraction

- **Brand**: "apple"
- **Model**: "iphone 16 pro"
- **Capacity**: "128gb"
- **Color**: "black titanium"

### Step 3: Matching

For each unmatched product:

1. **Search existing master products** with same brand
2. **Calculate similarity score** with each candidate
3. **If score ≥ 0.75**, link to existing master
4. **Else**, create new master product

### Step 4: Database Update

- Product's `master_product_id` field is set
- Master product's `search_tokens` are updated
- Changes are committed in batches (every 100 products)

---

## Matching Statistics

From the initial run on 231 products:

```
Total products processed: 231
Matched to existing masters: 58
New master products created: 173
```

**Analysis:**
- **58 products** were matched across stores (same product at Public and Stephanis)
- **173 unique products** were found (only available at one store)
- **Matching rate**: 25% of products have multi-store listings

---

## Maintenance & Tuning

### Adjusting Match Threshold

In `product_matcher.py`, adjust the threshold:

```python
def is_match(self, product1: Product, product2: Product, threshold: float = 0.7):
    # ...
    return score >= threshold  # Default: 0.7
```

- **Higher threshold** (0.8-0.9): More strict, fewer matches
- **Lower threshold** (0.5-0.6): More lenient, more matches (risk of false positives)

### Adding New Brands

Add to `BRANDS` list in `product_matcher.py`:

```python
BRANDS = [
    'apple', 'samsung', 'xiaomi', 'huawei', 'oppo',
    # Add your brands here
    'nokia', 'motorola', 'realme'
]
```

### Adding Model Patterns

Add regex patterns for new product types:

```python
model_patterns = [
    r'(iphone\s*\d+\s*(?:pro|plus|max|mini)?)',
    r'(galaxy\s*[a-z]\d+\s*(?:ultra|plus)?)',
    # Add new patterns here
    r'(xperia\s*\d+\s*(?:pro|compact)?)',
]
```

### Re-matching After Algorithm Changes

After improving the matching algorithm, rebuild all matches:

```bash
python product_matcher.py --rematch
```

This clears all existing matches and recreates them with the updated algorithm.

---

## Database Migration

For existing databases without the matching schema:

```bash
python migrate_db.py
```

This adds:
- `master_products` table
- `master_product_id` column to `products` table
- Required indexes

---

## Adding New Stores

The matching system works automatically with new stores:

1. Add new scraper (e.g., `MediaMarktScraper`)
2. Run `main.py`
3. Matching runs automatically on all new products
4. Products are linked to existing master products if matches found

No changes needed to the matching algorithm!

---

## Performance

### Current Performance (231 products):
- Matching time: ~10-15 seconds
- Memory usage: Minimal (loads all master products into memory)

### Scaling Considerations:

For **1,000-10,000 products**:
- No changes needed
- Matching time: ~1-2 minutes

For **100,000+ products**:
- Consider adding filtering before matching (by category, brand)
- Add database indexes on frequently queried fields
- Implement batch processing with pagination

### Optimization Ideas:

1. **Pre-filter by brand** - Only compare products with matching brands
2. **Category-based matching** - Only match within same category
3. **Cache normalized data** - Store normalized names in database
4. **Parallel processing** - Use multiprocessing for large batches

---

## API Integration (Future)

Example REST API endpoints you could build:

```
GET /api/products/search?q=iphone+16
GET /api/products/master/{id}
GET /api/products/compare?ids=1,2,3
GET /api/products/cheapest?category=smartphones
```

See `search_products.py` for ready-to-use query functions.

---

## Troubleshooting

### Products not matching that should

1. **Check brand extraction**:
   ```python
   matcher = ProductMatcher()
   print(matcher.extract_brand("Your Product Name"))
   ```

2. **Check similarity scores**:
   ```python
   score = matcher.calculate_similarity(name1, name2)
   print(f"Similarity: {score}")  # Should be > 0.7
   ```

3. **Lower threshold temporarily** to debug:
   ```python
   matcher.is_match(product1, product2, threshold=0.5)
   ```

### Too many false matches

1. **Increase threshold** to 0.8 or 0.9
2. **Check capacity matching** - ensure storage sizes are extracted correctly
3. **Add more model patterns** for your product types

### New brand not recognized

Add to `BRANDS` list and run `--rematch`

---

## Summary

✅ **Automatic matching** across stores
✅ **Fuzzy matching** handles name variations
✅ **Multi-strategy scoring** for accuracy
✅ **Easy to search** - find products by any terms
✅ **Scalable** - works with any number of stores
✅ **Maintainable** - simple to tune and improve

**Result:** Users can search "iphone 16 128gb" and instantly see price comparisons across all stores! 🎉
