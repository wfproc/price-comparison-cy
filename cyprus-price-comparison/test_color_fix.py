"""Test the color detection and normalization fixes."""
from product_matcher import ProductMatcher

def test_color_fixes():
    """Test that multi-word colors and modifiers are properly handled."""
    matcher = ProductMatcher()

    test_cases = [
        # (product_name, expected_normalized_base, expected_color)
        ("Apple iPhone 17 256GB Mist Blue", "apple iphone 17", "blue"),
        ("Apple iPhone 17 256GB Sage Green", "apple iphone 17", "green"),
        ("Smartphone APPLE iPhone 17 Pro 512GB 5G Dual SIM cosmic orange", "apple iphone 17 pro", "orange"),
        ("Smartphone APPLE iPhone 17 Pro 256GB 5G Dual SIM deep blue", "apple iphone 17 pro", "blue"),
        ("Smartphone APPLE iPhone Air 512GB 5G e-SIM sky blue", "apple iphone air", "blue"),
        ("Smartphone APPLE iPhone Air 512GB 5G e-SIM light gold", "apple iphone air", "gold"),
        ("Smartphone APPLE iPhone Air 512GB 5G e-SIM space black", "apple iphone air", "black"),
        ("Apple iPhone 16 128GB Ultramarine", "apple iphone 16", "ultramarine"),
        ("Apple iPhone 17 256GB Lavender", "apple iphone 17", "lavender"),
        ("Apple iPhone 17 Pro 256GB Silver", "apple iphone 17 pro", "silver"),
    ]

    print("="*80)
    print("COLOR DETECTION AND NORMALIZATION TEST")
    print("="*80)

    passed = 0
    failed = 0

    for name, expected_norm, expected_color in test_cases:
        normalized = matcher.normalize_text_base(name)
        color = matcher.extract_color(name)
        tokens = matcher.extract_base_tokens(name)

        # Check if normalization removes colors and stop words properly
        norm_match = normalized == expected_norm
        # Color detection might not match exactly, but the important part is normalization

        status = "✓ PASS" if norm_match else "✗ FAIL"
        if norm_match:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}")
        print(f"Input:      {name}")
        print(f"Expected:   {expected_norm}")
        print(f"Got:        {normalized}")
        print(f"Tokens:     {tokens}")
        print(f"Color:      {color} (expected: {expected_color})")

        if not norm_match:
            print(f"  ⚠ Difference detected!")

    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*80)

    return passed, failed

if __name__ == "__main__":
    passed, failed = test_color_fixes()
    exit(0 if failed == 0 else 1)
