"""Test that different model numbers correctly block matching."""
from product_matcher import ProductMatcher
from models import Product

def test_model_blocking():
    """Test that different models don't match (blocking factor)."""
    matcher = ProductMatcher()

    # Test cases: (product1_name, product2_name, should_match, reason)
    test_cases = [
        # Samsung A-series (SHOULD NOT MATCH)
        ("Samsung Galaxy A36 5G 256GB Awesome Black",
         "Samsung Galaxy A56 5G 256GB Awesome Graphite",
         False, "Different Samsung A-series models (A36 vs A56)"),

        ("Samsung Galaxy A36 128GB Black",
         "Samsung Galaxy A56 128GB Black",
         False, "Different Samsung A-series models (A36 vs A56)"),

        # Samsung S-series (SHOULD NOT MATCH)
        ("Samsung Galaxy S24 256GB Black",
         "Samsung Galaxy S25 256GB Black",
         False, "Different Samsung S-series models (S24 vs S25)"),

        ("Samsung Galaxy S25 Ultra 512GB Titanium Black",
         "Samsung Galaxy S25 256GB Silver",
         False, "Different models (S25 Ultra vs S25 - Ultra is a distinct model)"),

        ("Samsung Galaxy S25 512GB Black",
         "Samsung Galaxy S25 256GB Silver",
         True, "Same model (S25), different variants"),

        # iPhone models (SHOULD NOT MATCH)
        ("Apple iPhone 16 128GB Black",
         "Apple iPhone 17 128GB Black",
         False, "Different iPhone generations (16 vs 17)"),

        ("Apple iPhone 16 Pro 256GB Titanium",
         "Apple iPhone 16 128GB Black",
         False, "Different iPhone models (16 Pro vs 16)"),

        ("Apple iPhone 16 128GB Black",
         "Apple iPhone 16 256GB White",
         True, "Same iPhone model, different variants"),

        ("Apple iPhone 16E 128GB Black",
         "Apple iPhone 16 128GB Black",
         False, "Different iPhone variants (16E vs 16)"),

        # Samsung Z-series (SHOULD NOT MATCH)
        ("Samsung Galaxy Z Fold7 512GB Black",
         "Samsung Galaxy Z Flip7 512GB Black",
         False, "Different foldable models (Fold vs Flip)"),

        # Google Pixel (SHOULD NOT MATCH)
        ("Google Pixel 9 128GB Black",
         "Google Pixel 9 Pro 128GB Black",
         False, "Different Pixel models (9 vs 9 Pro)"),

        # Same products with store-specific formatting (SHOULD MATCH)
        ("Apple iPhone 17 256GB Mist Blue",
         "Smartphone APPLE iPhone 17 256GB 5G Dual SIM white",
         True, "Same iPhone 17, different stores"),

        ("Samsung Galaxy A36 5G 256GB Awesome Black",
         "Samsung Galaxy A36 5G 256GB Awesome Lavender",
         True, "Same Samsung A36, different colors"),
    ]

    print("=" * 80)
    print("MODEL NUMBER BLOCKING TEST")
    print("=" * 80)

    passed = 0
    failed = 0

    for name1, name2, expected_match, reason in test_cases:
        # Create mock Product objects
        p1 = Product(name=name1, price=100.0, store="test", store_product_id="1",
                     url="http://test.com/1", brand="Test")
        p2 = Product(name=name2, price=100.0, store="test", store_product_id="2",
                     url="http://test.com/2", brand="Test")

        actual_match = matcher.is_match(p1, p2)

        # Extract models for debugging
        brand1 = matcher.extract_brand(name1)
        brand2 = matcher.extract_brand(name2)
        model1 = matcher.extract_model(name1, brand1)
        model2 = matcher.extract_model(name2, brand2)

        test_passed = (actual_match == expected_match)
        status = "✓ PASS" if test_passed else "✗ FAIL"

        if test_passed:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}: {reason}")
        print(f"  Product 1: {name1}")
        print(f"  Product 2: {name2}")
        print(f"  Model 1: {model1}")
        print(f"  Model 2: {model2}")
        print(f"  Expected match: {expected_match}")
        print(f"  Actual match:   {actual_match}")

        if not test_passed:
            print(f"  ⚠ MISMATCH DETECTED!")

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return passed, failed

if __name__ == "__main__":
    passed, failed = test_model_blocking()
    exit(0 if failed == 0 else 1)
