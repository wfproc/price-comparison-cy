"""Search for products across stores using the master product grouping."""
from typing import List, Dict
from models import Product, MasterProduct, get_session
from product_matcher import ProductMatcher


def search_products(query: str, limit: int = 20) -> List[Dict]:
    """
    Search for products by query string.
    Returns master products with all their store variants.

    Example:
        results = search_products("iphone 16 128gb")
        # Returns all stores selling iPhone 16 128GB
    """
    session = get_session()
    matcher = ProductMatcher()

    try:
        # Normalize the search query
        normalized_query = matcher.normalize_text(query)
        tokens = matcher.extract_tokens(query)

        results = []

        # Search master products
        masters = session.query(MasterProduct).filter(
            MasterProduct.normalized_name.like(f"%{normalized_query}%")
        ).limit(limit).all()

        # If no direct match, try token-based search
        if not masters and tokens:
            masters = session.query(MasterProduct).all()
            # Filter by token overlap
            scored_masters = []
            for master in masters:
                master_tokens = master.search_tokens.split() if master.search_tokens else []
                overlap = matcher.calculate_token_overlap(tokens, master_tokens)
                if overlap >= 0.3:  # At least 30% token overlap
                    scored_masters.append((master, overlap))

            # Sort by score and take top results
            scored_masters.sort(key=lambda x: x[1], reverse=True)
            masters = [m[0] for m in scored_masters[:limit]]

        # For each master product, get all store variants
        for master in masters:
            products = session.query(Product).filter(
                Product.master_product_id == master.id
            ).all()

            if not products:
                continue

            # Find cheapest price
            prices = [p.price for p in products if p.price > 0]
            cheapest_price = min(prices) if prices else 0
            most_expensive = max(prices) if prices else 0

            result = {
                'master_id': master.id,
                'name': master.canonical_name,
                'brand': master.brand,
                'model': master.model,
                'category': master.category,
                'cheapest_price': cheapest_price,
                'most_expensive': most_expensive,
                'price_difference': most_expensive - cheapest_price if prices else 0,
                'store_count': len(products),
                'stores': []
            }

            # Add store-specific information
            for product in products:
                result['stores'].append({
                    'store': product.store,
                    'price': product.price,
                    'url': product.url,
                    'name': product.name,
                    'availability': product.availability,
                    'original_price': product.original_price,
                    'discount_percentage': product.discount_percentage
                })

            # Sort stores by price
            result['stores'].sort(key=lambda x: x['price'])

            results.append(result)

        return results

    finally:
        session.close()


def compare_prices(product_name: str):
    """
    Compare prices for a specific product across all stores.
    Prints a formatted comparison.
    """
    results = search_products(product_name, limit=5)

    if not results:
        print(f"\nNo products found matching: {product_name}")
        return

    print(f"\n{'='*80}")
    print(f"PRICE COMPARISON: {product_name}")
    print(f"{'='*80}\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']}")
        if result['brand']:
            print(f"   Brand: {result['brand']}")
        if result['model']:
            print(f"   Model: {result['model']}")

        print(f"\n   Found in {result['store_count']} store(s):")
        print(f"   Cheapest: €{result['cheapest_price']:.2f}")
        print(f"   Most expensive: €{result['most_expensive']:.2f}")

        if result['price_difference'] > 0:
            savings_pct = (result['price_difference'] / result['most_expensive']) * 100
            print(f"   SAVE EUR{result['price_difference']:.2f} ({savings_pct:.1f}%) by choosing cheapest!")

        print(f"\n   Store prices:")
        for store_data in result['stores']:
            price_str = f"€{store_data['price']:.2f}"
            discount_str = ""
            if store_data['discount_percentage']:
                discount_str = f" (-{store_data['discount_percentage']:.0f}%)"

            availability = ""
            if store_data['availability'] == 'out_of_stock':
                availability = " [OUT OF STOCK]"
            elif store_data['availability'] == 'pre_order':
                availability = " [PRE-ORDER]"

            print(f"     • {store_data['store'].upper():12s} {price_str:>10s}{discount_str}{availability}")
            print(f"       {store_data['url']}")

        print()


def get_best_deals(store: str = None, limit: int = 10) -> List[Dict]:
    """
    Get products with the best discounts or prices.

    Args:
        store: Filter by specific store (optional)
        limit: Number of results to return

    Returns:
        List of products sorted by discount or price
    """
    session = get_session()

    try:
        query = session.query(Product)

        if store:
            query = query.filter(Product.store == store)

        # Get products with discounts
        products = query.filter(
            Product.discount_percentage.isnot(None),
            Product.discount_percentage > 0
        ).order_by(Product.discount_percentage.desc()).limit(limit).all()

        results = []
        for product in products:
            results.append({
                'store': product.store,
                'name': product.name,
                'price': product.price,
                'original_price': product.original_price,
                'discount_percentage': product.discount_percentage,
                'savings': product.original_price - product.price if product.original_price else 0,
                'url': product.url
            })

        return results

    finally:
        session.close()


def get_product_by_master_id(master_id: int) -> Dict:
    """Get all store variants for a specific master product."""
    session = get_session()

    try:
        master = session.query(MasterProduct).filter(MasterProduct.id == master_id).first()

        if not master:
            return None

        products = session.query(Product).filter(
            Product.master_product_id == master_id
        ).all()

        result = {
            'master_id': master.id,
            'name': master.canonical_name,
            'brand': master.brand,
            'model': master.model,
            'stores': []
        }

        for product in products:
            result['stores'].append({
                'store': product.store,
                'price': product.price,
                'url': product.url,
                'name': product.name
            })

        return result

    finally:
        session.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python search_products.py <search query>")
        print("Example: python search_products.py 'iphone 16 128gb'")
        sys.exit(1)

    query = ' '.join(sys.argv[1:])
    compare_prices(query)
