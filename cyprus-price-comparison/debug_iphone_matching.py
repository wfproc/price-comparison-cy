"""Debug script to analyze iPhone matching issues between stores."""
from models import Product, MasterProduct, get_session
from product_matcher import ProductMatcher
import re

def analyze_iphone_products():
    """Analyze iPhone products from different stores."""
    session = get_session()
    matcher = ProductMatcher()

    # Get iPhone products from Public and Stephanis
    public_iphones = session.query(Product).filter(
        Product.store == 'public',
        Product.name.ilike('%iphone%')
    ).all()

    stephanis_iphones = session.query(Product).filter(
        Product.store == 'stephanis',
        Product.name.ilike('%iphone%')
    ).all()

    print("=" * 80)
    print("IPHONE PRODUCTS ANALYSIS")
    print("=" * 80)

    print(f"\n{'PUBLIC STORE':-^80}")
    print(f"Found {len(public_iphones)} iPhone products\n")
    for p in public_iphones[:10]:  # Show first 10
        print(f"ID: {p.id}")
        print(f"  Name: {p.name}")
        print(f"  Brand: {p.brand}")
        print(f"  Price: €{p.price}")
        print(f"  Master ID: {p.master_product_id}")
        print(f"  Variant ID: {p.variant_id}")

        # Test normalization
        normalized = matcher.normalize_text_base(p.name)
        tokens = matcher.extract_base_tokens(p.name)
        brand = matcher._normalize_brand(p.brand) or matcher.extract_brand(p.name)
        model = matcher.extract_model(p.name, brand)
        capacity = matcher.extract_capacity(p.name)
        color = matcher.extract_color(p.name)

        print(f"  Normalized (base): {normalized}")
        print(f"  Tokens: {tokens}")
        print(f"  Extracted Brand: {brand}")
        print(f"  Extracted Model: {model}")
        print(f"  Extracted Capacity: {capacity}")
        print(f"  Extracted Color: {color}")
        print()

    print(f"\n{'STEPHANIS STORE':-^80}")
    print(f"Found {len(stephanis_iphones)} iPhone products\n")
    for p in stephanis_iphones[:10]:  # Show first 10
        print(f"ID: {p.id}")
        print(f"  Name: {p.name}")
        print(f"  Brand: {p.brand}")
        print(f"  Price: €{p.price}")
        print(f"  Master ID: {p.master_product_id}")
        print(f"  Variant ID: {p.variant_id}")

        # Test normalization
        normalized = matcher.normalize_text_base(p.name)
        tokens = matcher.extract_base_tokens(p.name)
        brand = matcher._normalize_brand(p.brand) or matcher.extract_brand(p.name)
        model = matcher.extract_model(p.name, brand)
        capacity = matcher.extract_capacity(p.name)
        color = matcher.extract_color(p.name)

        print(f"  Normalized (base): {normalized}")
        print(f"  Tokens: {tokens}")
        print(f"  Extracted Brand: {brand}")
        print(f"  Extracted Model: {model}")
        print(f"  Extracted Capacity: {capacity}")
        print(f"  Extracted Color: {color}")
        print()

    # Test matching between stores
    print(f"\n{'MATCHING TEST':-^80}")
    if public_iphones and stephanis_iphones:
        print("\nTesting if products would match:")
        for pub in public_iphones[:3]:
            print(f"\nPublic: {pub.name}")
            for step in stephanis_iphones[:3]:
                print(f"  vs Stephanis: {step.name}")
                would_match = matcher.is_match(pub, step)

                # Show detailed comparison
                pub_norm = matcher.normalize_text_base(pub.name)
                step_norm = matcher.normalize_text_base(step.name)
                similarity = matcher.calculate_similarity_base(pub.name, step.name)

                pub_tokens = matcher.extract_base_tokens(pub.name)
                step_tokens = matcher.extract_base_tokens(step.name)
                token_overlap = matcher.calculate_token_overlap(pub_tokens, step_tokens)

                print(f"    Match: {would_match}")
                print(f"    Name similarity: {similarity:.2f}")
                print(f"    Token overlap: {token_overlap:.2f}")
                print(f"    Public normalized: {pub_norm}")
                print(f"    Stephanis normalized: {step_norm}")
                print(f"    Public tokens: {pub_tokens}")
                print(f"    Stephanis tokens: {step_tokens}")

    # Check existing master products for iPhones
    print(f"\n{'EXISTING MASTER PRODUCTS':-^80}")
    master_iphones = session.query(MasterProduct).filter(
        MasterProduct.canonical_name.ilike('%iphone%')
    ).all()

    print(f"Found {len(master_iphones)} iPhone master products\n")
    for master in master_iphones[:10]:
        print(f"Master ID: {master.id}")
        print(f"  Canonical Name: {master.canonical_name}")
        print(f"  Brand: {master.brand}")
        print(f"  Model: {master.model}")
        print(f"  Normalized: {master.normalized_name}")
        print(f"  Search Tokens: {master.search_tokens}")

        # Count linked products
        linked_count = len(master.products)
        stores = set(p.store for p in master.products)
        print(f"  Linked Products: {linked_count} from stores: {stores}")
        print()

    session.close()

if __name__ == "__main__":
    analyze_iphone_products()
