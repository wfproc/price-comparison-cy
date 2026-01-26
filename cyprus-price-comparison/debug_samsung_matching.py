"""Debug script to analyze Samsung A36/A56 matching issues."""
from models import Product, MasterProduct, get_session
from product_matcher import ProductMatcher
import re

def analyze_samsung_products():
    """Analyze Samsung products to identify matching issues."""
    session = get_session()
    matcher = ProductMatcher()

    # Get Samsung A36 and A56 products
    a36_products = session.query(Product).filter(
        Product.name.ilike('%samsung%a36%')
    ).all()

    a56_products = session.query(Product).filter(
        Product.name.ilike('%samsung%a56%')
    ).all()

    print("=" * 80)
    print("SAMSUNG A-SERIES MATCHING ANALYSIS")
    print("=" * 80)

    print(f"\n{'SAMSUNG A36 PRODUCTS':-^80}")
    print(f"Found {len(a36_products)} products\n")
    for p in a36_products[:5]:
        print(f"ID: {p.id} | Store: {p.store}")
        print(f"  Name: {p.name}")
        print(f"  Price: €{p.price}")
        print(f"  Master ID: {p.master_product_id}")

        normalized = matcher.normalize_text_base(p.name)
        tokens = matcher.extract_base_tokens(p.name)
        brand = matcher._normalize_brand(p.brand) or matcher.extract_brand(p.name)
        model = matcher.extract_model(p.name, brand)
        capacity = matcher.extract_capacity(p.name)

        print(f"  Normalized (base): {normalized}")
        print(f"  Tokens: {tokens}")
        print(f"  Extracted Brand: {brand}")
        print(f"  Extracted Model: {model}")
        print(f"  Extracted Capacity: {capacity}")
        print()

    print(f"\n{'SAMSUNG A56 PRODUCTS':-^80}")
    print(f"Found {len(a56_products)} products\n")
    for p in a56_products[:5]:
        print(f"ID: {p.id} | Store: {p.store}")
        print(f"  Name: {p.name}")
        print(f"  Price: €{p.price}")
        print(f"  Master ID: {p.master_product_id}")

        normalized = matcher.normalize_text_base(p.name)
        tokens = matcher.extract_base_tokens(p.name)
        brand = matcher._normalize_brand(p.brand) or matcher.extract_brand(p.name)
        model = matcher.extract_model(p.name, brand)
        capacity = matcher.extract_capacity(p.name)

        print(f"  Normalized (base): {normalized}")
        print(f"  Tokens: {tokens}")
        print(f"  Extracted Brand: {brand}")
        print(f"  Extracted Model: {model}")
        print(f"  Extracted Capacity: {capacity}")
        print()

    # Test if A36 and A56 would match
    if a36_products and a56_products:
        print(f"\n{'CROSS-MODEL MATCHING TEST':-^80}")
        a36 = a36_products[0]
        a56 = a56_products[0]

        print(f"\nTesting: {a36.name}")
        print(f"     vs: {a56.name}")

        would_match = matcher.is_match(a36, a56)

        # Detailed comparison
        a36_norm = matcher.normalize_text_base(a36.name)
        a56_norm = matcher.normalize_text_base(a56.name)
        similarity = matcher.calculate_similarity_base(a36.name, a56.name)

        a36_tokens = matcher.extract_base_tokens(a36.name)
        a56_tokens = matcher.extract_base_tokens(a56.name)
        token_overlap = matcher.calculate_token_overlap(a36_tokens, a56_tokens)

        a36_model = matcher.extract_model(a36.name, 'samsung')
        a56_model = matcher.extract_model(a56.name, 'samsung')

        print(f"\n  Match Result: {would_match}")
        print(f"  Name similarity: {similarity:.2f}")
        print(f"  Token overlap: {token_overlap:.2f}")
        print(f"  A36 normalized: {a36_norm}")
        print(f"  A56 normalized: {a56_norm}")
        print(f"  A36 tokens: {a36_tokens}")
        print(f"  A56 tokens: {a56_tokens}")
        print(f"  A36 model: {a36_model}")
        print(f"  A56 model: {a56_model}")

        if would_match:
            print("\n  ⚠ ERROR: These different models SHOULD NOT match!")
        else:
            print("\n  ✓ CORRECT: These different models are properly separated")

    # Check master products
    print(f"\n{'MASTER PRODUCTS':-^80}")
    samsung_a_masters = session.query(MasterProduct).filter(
        MasterProduct.canonical_name.ilike('%samsung%a__%')
    ).all()

    print(f"Found {len(samsung_a_masters)} Samsung A-series master products\n")
    for master in samsung_a_masters[:10]:
        print(f"Master ID: {master.id}")
        print(f"  Name: {master.canonical_name}")
        print(f"  Model: {master.model}")
        print(f"  Normalized: {master.normalized_name}")

        linked = master.products
        stores = set(p.store for p in linked)
        product_names = set(p.name[:50] for p in linked[:3])

        print(f"  Linked: {len(linked)} products from {stores}")
        print(f"  Sample products:")
        for name in list(product_names)[:3]:
            print(f"    - {name}")
        print()

    session.close()

if __name__ == "__main__":
    analyze_samsung_products()
