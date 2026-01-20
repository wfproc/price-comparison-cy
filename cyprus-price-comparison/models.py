"""Database models for normalized product data."""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

Base = declarative_base()

class MasterProduct(Base):
    """Master product record - single source of truth for a product across stores."""
    __tablename__ = "master_products"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Canonical product information
    canonical_name = Column(String(500), nullable=False)
    brand = Column(String(100), index=True)
    model = Column(String(200), index=True)
    category = Column(String(100), index=True)

    # Normalized search fields (for matching)
    normalized_name = Column(String(500), nullable=False, index=True)  # Lowercase, no special chars
    search_tokens = Column(Text)  # Space-separated tokens for matching

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to products
    products = relationship("Product", back_populates="master_product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MasterProduct(id={self.id}, name={self.canonical_name[:50]})>"


class Product(Base):
    """Normalized product model for price comparison."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Product identification
    store = Column(String(50), nullable=False, index=True)
    store_product_id = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)

    # Link to master product (single source of truth) with foreign key constraint
    master_product_id = Column(Integer, ForeignKey('master_products.id', ondelete='SET NULL'), index=True)
    
    # Product details
    name = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    brand = Column(String(100), index=True)
    
    # Pricing
    price = Column(Float, nullable=False, index=True)
    currency = Column(String(10), default="EUR")
    original_price = Column(Float)  # For discounted items
    discount_percentage = Column(Float)
    
    # Additional metadata
    image_url = Column(Text)
    availability = Column(String(50))  # "in_stock", "out_of_stock", "pre_order"
    specifications = Column(Text)  # JSON string of key-value pairs
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to master product
    master_product = relationship("MasterProduct", back_populates="products")

    # Relationship to price history
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    # Composite index for store + product_id uniqueness
    __table_args__ = (
        Index("idx_store_product", "store", "store_product_id", unique=True),
    )

    def __repr__(self):
        return f"<Product(store={self.store}, name={self.name[:50]}, price={self.price})>"


class PriceHistory(Base):
    """Track price changes over time."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="EUR")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship to product
    product = relationship("Product", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, timestamp={self.timestamp})>"


def get_engine():
    """Get database engine."""
    return create_engine(config.DATABASE_URL, echo=False)


def get_session():
    """Get database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print(f"Database initialized at {config.DATABASE_URL}")
