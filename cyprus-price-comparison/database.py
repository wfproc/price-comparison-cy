"""Database operations for storing and retrieving products."""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.exc import IntegrityError
from models import Product, PriceHistory, get_session, init_db
from datetime import datetime


def save_products(products: List[Dict]) -> Tuple[int, int]:
    """
    Save products to database.
    Returns (created_count, updated_count).
    """
    session = get_session()
    created = 0
    updated = 0
    
    try:
        for product_data in products:
            # Check if product exists
            existing = session.query(Product).filter_by(
                store=product_data["store"],
                store_product_id=product_data["store_product_id"]
            ).first()
            
            if existing:
                # Update existing product
                old_price = existing.price
                for key, value in product_data.items():
                    if key not in ["store", "store_product_id"]:
                        setattr(existing, key, value)
                existing.last_updated = datetime.utcnow()
                
                # Record price change if different
                if old_price != existing.price:
                    price_history = PriceHistory(
                        product_id=existing.id,
                        price=existing.price,
                        currency=existing.currency
                    )
                    session.add(price_history)
                
                updated += 1
            else:
                # Create new product
                product = Product(**product_data)
                session.add(product)
                created += 1
                
                # Create initial price history entry
                session.flush()  # Get product ID
                price_history = PriceHistory(
                    product_id=product.id,
                    price=product.price,
                    currency=product.currency
                )
                session.add(price_history)
        
        session.commit()
        return created, updated
        
    except IntegrityError as e:
        session.rollback()
        print(f"[WARNING] Database integrity error: {e}")
        return created, updated
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error saving products: {e}")
        raise
    finally:
        session.close()


def get_products(store: Optional[str] = None, category: Optional[str] = None) -> List[Product]:
    """Get products from database with optional filters."""
    session = get_session()
    try:
        query = session.query(Product)
        
        if store:
            query = query.filter(Product.store == store)
        if category:
            query = query.filter(Product.category == category)
        
        return query.all()
    finally:
        session.close()


def get_price_comparison(product_name: str, limit: int = 10) -> List[Dict]:
    """Get price comparison for products with similar names."""
    session = get_session()
    try:
        products = session.query(Product).filter(
            Product.name.ilike(f"%{product_name}%")
        ).order_by(Product.price).limit(limit).all()
        
        return [{
            "store": p.store,
            "name": p.name,
            "price": p.price,
            "currency": p.currency,
            "url": p.url,
            "availability": p.availability
        } for p in products]
    finally:
        session.close()
