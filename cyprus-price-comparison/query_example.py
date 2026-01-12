"""Example script for querying the product database."""
from database import get_products, get_price_comparison
from models import get_session, Product
from sqlalchemy import func


def print_product(product):
    """Print product information."""
    print(f"  {product.name[:60]}")
    print(f"    Store: {product.store} | Price: {product.price} {product.currency}")
    print(f"    URL: {product.url}")
    print(f"    Availability: {product.availability}")
    print()


def main():
    """Example queries."""
    print("="*60)
    print("PRODUCT DATABASE QUERIES")
    print("="*60)
    print()
    
    session = get_session()
    try:
        # Get total product count
        total = session.query(Product).count()
        print(f"Total products in database: {total}\n")
        
        # Get products by store
        print("Products by store:")
        stores = session.query(Product.store, func.count(Product.id)).group_by(Product.store).all()
        for store, count in stores:
            print(f"  {store}: {count} products")
        print()
        
        # Get products by category
        print("Products by category:")
        categories = session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
        for category, count in categories:
            if category:
                print(f"  {category}: {count} products")
        print()
        
        # Get cheapest products
        print("Top 10 cheapest products:")
        cheapest = session.query(Product).order_by(Product.price).limit(10).all()
        for product in cheapest:
            print_product(product)
        
        # Example: Search for a specific product
        print("\n" + "="*60)
        print("Price comparison example: 'iPhone'")
        print("="*60)
        comparison = get_price_comparison("iPhone", limit=5)
        if comparison:
            for item in comparison:
                print(f"  {item['name'][:60]}")
                print(f"    {item['store']}: {item['price']} {item['currency']}")
                print(f"    {item['url']}")
                print()
        else:
            print("  No products found matching 'iPhone'")
        
        # Get products from a specific store
        print("\n" + "="*60)
        print("Products from Public Cyprus:")
        print("="*60)
        public_products = get_products(store="public")
        print(f"Found {len(public_products)} products from Public Cyprus")
        if public_products:
            print("\nFirst 5 products:")
            for product in public_products[:5]:
                print_product(product)
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
