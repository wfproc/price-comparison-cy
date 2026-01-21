"""Product matching system to group products across stores."""
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from models import Product, MasterProduct, MasterProductVariant, get_session


class ProductMatcher:
    """Match products across stores using fuzzy matching and normalization."""

    # Common brand names to recognize
    BRANDS = [
        'apple', 'samsung', 'xiaomi', 'huawei', 'oppo', 'oneplus', 'google', 'nokia',
        'sony', 'lg', 'lenovo', 'asus', 'acer', 'hp', 'dell', 'msi', 'razer',
        'microsoft', 'logitech', 'corsair', 'steelseries', 'hyperx', 'intel', 'amd',
        'nvidia', 'bosch', 'philips', 'panasonic', 'canon', 'nikon', 'gopro'
    ]

    # Words to remove during normalization (meaningless for matching)
    STOP_WORDS = [
        'smartphone', 'tablet', 'laptop', 'notebook', 'desktop', 'computer',
        'new', 'original', 'genuine', 'official', 'unlocked', 'sealed',
        'dual', 'sim', 'wifi', 'wi-fi', 'bluetooth', 'inch', 'screen'
    ]

    # Unit conversions and normalizations
    UNIT_PATTERNS = [
        (r'(\d+)\s*gb', r'\1gb'),       # "128 GB" -> "128gb"
        (r'(\d+)\s*tb', r'\1tb'),       # "1 TB" -> "1tb"
        (r'(\d+)\s*mb', r'\1mb'),       # "512 MB" -> "512mb"
        (r'(\d+)"', r'\1inch'),         # 6.5" -> 6.5inch
        (r'(\d+)\'', r'\1inch'),        # 6.5' -> 6.5inch
    ]

    CAPACITY_PATTERN = r'\b\d+(?:gb|tb|mb)\b'

    COLOR_WORDS = [
        'black', 'white', 'silver', 'gold', 'blue', 'red', 'green', 'yellow',
        'pink', 'purple', 'gray', 'grey', 'orange', 'titanium', 'bronze',
        'midnight', 'starlight', 'sierra', 'graphite', 'rose', 'space', 'natural'
    ]

    def __init__(self):
        self.session = get_session()

    def normalize_text(self, text: str) -> str:
        """Normalize text for matching: lowercase, remove special chars, standardize units."""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower().strip()

        # Normalize units
        for pattern, replacement in self.UNIT_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)

        # Remove extra spaces
        text = ' '.join(text.split())

        return text

    def normalize_text_base(self, text: str) -> str:
        """Normalize text for master matching by removing capacity and color tokens."""
        normalized = self.normalize_text(text)
        normalized = re.sub(self.CAPACITY_PATTERN, '', normalized)
        tokens = [t for t in normalized.split() if t not in self.COLOR_WORDS]
        return ' '.join(tokens)

    def extract_base_tokens(self, text: str) -> List[str]:
        """Extract tokens for master matching (ignores capacity/color)."""
        normalized = self.normalize_text_base(text)
        tokens = normalized.split()
        tokens = [t for t in tokens if t not in self.STOP_WORDS]
        return tokens

    def build_base_name(self, name: str) -> str:
        """Build a display-friendly base name by removing capacity and color."""
        if not name:
            return ""
        base = re.sub(r'\b\d+\s*(?:gb|tb|mb)\b', '', name, flags=re.IGNORECASE)
        color = self.extract_color(base)
        if color:
            base = re.sub(r'\b' + re.escape(color) + r'\b', '', base, flags=re.IGNORECASE)
        base = re.sub(r'\s+', ' ', base).strip()
        return base or name

    def extract_tokens(self, text: str) -> List[str]:
        """Extract meaningful tokens from text, removing stop words."""
        normalized = self.normalize_text(text)
        tokens = normalized.split()

        # Remove stop words
        tokens = [t for t in tokens if t not in self.STOP_WORDS]

        return tokens

    def extract_brand(self, name: str) -> Optional[str]:
        """Extract brand name from product name."""
        normalized = self.normalize_text(name)
        tokens = normalized.split()

        for token in tokens:
            if token in self.BRANDS:
                return token

        # Check if any brand is a substring
        for brand in self.BRANDS:
            if brand in normalized:
                return brand

        return None

    def extract_model(self, name: str, brand: Optional[str]) -> Optional[str]:
        """Extract model identifier from product name."""
        normalized = self.normalize_text(name)

        # Remove brand from name to focus on model
        if brand:
            normalized = normalized.replace(brand, '').strip()

        # Look for common model patterns
        # e.g., "iphone 16 pro", "galaxy s24", "xperia 1 v"
        model_patterns = [
            r'(iphone\s*\d+\s*(?:pro|plus|max|mini)?)',
            r'(galaxy\s*[a-z]\d+\s*(?:ultra|plus)?)',
            r'(pixel\s*\d+\s*(?:pro|xl)?)',
            r'(ipad\s*(?:pro|air|mini)?\s*\d*)',
            r'(macbook\s*(?:pro|air)?\s*\d*)',
            r'([a-z]+\s*\d+\s*(?:pro|plus|max|ultra)?)',  # Generic: model + number
        ]

        for pattern in model_patterns:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def extract_capacity(self, name: str) -> Optional[str]:
        """Extract storage capacity (e.g., 128gb, 256gb, 1tb)."""
        normalized = self.normalize_text(name)

        # Look for storage patterns
        capacity_match = re.search(r'(\d+(?:gb|tb|mb))', normalized)
        if capacity_match:
            return capacity_match.group(1)

        return None

    def extract_color(self, name: str) -> Optional[str]:
        """Extract color from product name."""
        colors = [
            'black', 'white', 'silver', 'gold', 'blue', 'red', 'green', 'yellow',
            'pink', 'purple', 'gray', 'grey', 'orange', 'titanium', 'bronze',
            'midnight', 'starlight', 'sierra', 'graphite', 'rose'
        ]

        normalized = self.normalize_text(name)
        tokens = normalized.split()

        for token in tokens:
            if token in colors:
                return token

        # Check for multi-word colors (e.g., "space gray", "midnight blue")
        for i in range(len(tokens) - 1):
            two_word = f"{tokens[i]} {tokens[i+1]}"
            if any(color in two_word for color in colors):
                return two_word

        return None

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity score between two texts (0.0 to 1.0)."""
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()

    def calculate_similarity_base(self, text1: str, text2: str) -> float:
        """Calculate similarity score using base normalization (ignores capacity/color)."""
        norm1 = self.normalize_text_base(text1)
        norm2 = self.normalize_text_base(text2)
        return SequenceMatcher(None, norm1, norm2).ratio()

    def calculate_token_overlap(self, tokens1: List[str], tokens2: List[str]) -> float:
        """Calculate token overlap ratio (Jaccard similarity)."""
        if not tokens1 or not tokens2:
            return 0.0

        set1 = set(tokens1)
        set2 = set(tokens2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def is_match(self, product1: Product, product2: Product, threshold: float = 0.7) -> bool:
        """
        Determine if two products are the same.
        Uses multiple matching strategies with weighted scoring.
        """
        # Extract features
        brand1 = product1.brand or self.extract_brand(product1.name)
        brand2 = product2.brand or self.extract_brand(product2.name)

        # If brands are explicitly different, not a match
        if brand1 and brand2 and brand1.lower() != brand2.lower():
            return False

        # Calculate various similarity scores
        name_similarity = self.calculate_similarity_base(product1.name, product2.name)

        tokens1 = self.extract_base_tokens(product1.name)
        tokens2 = self.extract_base_tokens(product2.name)
        token_overlap = self.calculate_token_overlap(tokens1, tokens2)

        # Check for matching capacity
        cap1 = self.extract_capacity(product1.name)
        cap2 = self.extract_capacity(product2.name)
        capacity_match = cap1 == cap2 if cap1 and cap2 else True  # If no capacity, don't penalize

        # Check for matching model
        model1 = self.extract_model(product1.name, brand1)
        model2 = self.extract_model(product2.name, brand2)
        model_match = model1 == model2 if model1 and model2 else True

        # Weighted scoring
        score = (
            name_similarity * 0.4 +
            token_overlap * 0.4 +
            (1.0 if capacity_match else 0.0) * 0.1 +
            (1.0 if model_match else 0.0) * 0.1
        )

        return score >= threshold

    def find_matching_master_product(self, product: Product) -> Optional[MasterProduct]:
        """Find existing master product that matches this product."""
        # Get all master products (in production, you'd want pagination/filtering)
        master_products = self.session.query(MasterProduct).all()

        best_match = None
        best_score = 0.0

        for master in master_products:
            # Quick filtering by brand
            if master.brand and product.brand:
                if master.brand.lower() != product.brand.lower():
                    continue

            # Calculate similarity using base normalization
            name_sim = self.calculate_similarity_base(product.name, master.canonical_name)
            tokens_product = self.extract_base_tokens(product.name)
            tokens_master = master.search_tokens.split() if master.search_tokens else []
            token_overlap = self.calculate_token_overlap(tokens_product, tokens_master)

            score = name_sim * 0.6 + token_overlap * 0.4

            if score > best_score:
                best_score = score
                best_match = master

        # Return match if score is high enough
        if best_match and best_score >= 0.75:
            return best_match

        return None

    def create_master_product(self, product: Product) -> MasterProduct:
        """Create a new master product from a product."""
        brand = product.brand or self.extract_brand(product.name)
        model = self.extract_model(product.name, brand)
        base_name = self.build_base_name(product.name)

        master = MasterProduct(
            canonical_name=base_name,
            brand=brand,
            model=model,
            category=product.category,
            normalized_name=self.normalize_text_base(base_name),
            search_tokens=' '.join(self.extract_base_tokens(base_name))
        )

        self.session.add(master)
        self.session.flush()  # Get the ID

        return master

    def get_or_create_variant(self, master: MasterProduct, product: Product) -> MasterProductVariant:
        """Get or create a variant under a master product based on capacity."""
        capacity = self.extract_capacity(product.name)
        if not capacity:
            capacity = "unknown"

        variant = self.session.query(MasterProductVariant).filter(
            MasterProductVariant.master_product_id == master.id,
            MasterProductVariant.capacity == capacity
        ).first()

        if variant:
            return variant

        variant = MasterProductVariant(
            master_product_id=master.id,
            capacity=capacity
        )
        self.session.add(variant)
        self.session.flush()
        return variant

    def match_products(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Match all products to master products.
        Creates master products as needed.
        Returns statistics.
        """
        stats = {
            'total_products': 0,
            'matched_to_existing': 0,
            'new_master_created': 0,
            'already_matched': 0
        }

        # Get unmatched products or products missing variant assignment
        products = self.session.query(Product).filter(
            (Product.master_product_id.is_(None)) | (Product.variant_id.is_(None))
        ).all()

        stats['total_products'] = len(products)
        print(f"\nMatching {len(products)} unmatched products...")

        for i, product in enumerate(products):
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(products)}")

            master = None
            if product.master_product_id:
                master = self.session.query(MasterProduct).get(product.master_product_id)
                if master:
                    stats['already_matched'] += 1
                else:
                    product.master_product_id = None

            if not master:
                # Try to find matching master product
                master = self.find_matching_master_product(product)

                if master:
                    # Link to existing master product
                    product.master_product_id = master.id
                    stats['matched_to_existing'] += 1
                else:
                    # Create new master product
                    master = self.create_master_product(product)
                    product.master_product_id = master.id
                    stats['new_master_created'] += 1

            variant = self.get_or_create_variant(master, product)
            product.variant_id = variant.id

            # Commit in batches
            if (i + 1) % batch_size == 0:
                self.session.commit()

        # Final commit
        self.session.commit()

        return stats

    def rematch_all_products(self) -> Dict[str, int]:
        """
        Re-match all products from scratch.
        Clears existing matches and recreates master products.
        Use this to rebuild the matching after algorithm improvements.
        """
        print("\n[WARNING] Clearing all existing matches...")

        # Clear all master_product_id and variant_id links
        self.session.query(Product).update({Product.master_product_id: None, Product.variant_id: None})

        # Delete all master products and variants
        self.session.query(MasterProductVariant).delete()
        self.session.query(MasterProduct).delete()
        self.session.commit()

        print("[OK] Cleared existing matches")

        # Now run matching
        return self.match_products()

    def close(self):
        """Close database session."""
        self.session.close()


def run_product_matching(rematch: bool = False):
    """Main function to run product matching."""
    matcher = ProductMatcher()

    try:
        if rematch:
            stats = matcher.rematch_all_products()
        else:
            stats = matcher.match_products()

        print("\n" + "=" * 60)
        print("PRODUCT MATCHING RESULTS")
        print("=" * 60)
        print(f"Total products processed: {stats['total_products']}")
        print(f"Matched to existing masters: {stats['matched_to_existing']}")
        print(f"New master products created: {stats['new_master_created']}")
        print(f"Already matched: {stats['already_matched']}")
        print("=" * 60 + "\n")

        return stats
    finally:
        matcher.close()


if __name__ == "__main__":
    import sys
    rematch = '--rematch' in sys.argv
    run_product_matching(rematch=rematch)
