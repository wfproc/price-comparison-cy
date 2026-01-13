"""Migrate existing database to add master products and linking."""
import sqlite3
from pathlib import Path
import config


def migrate_database():
    """Add master_products table and master_product_id column to products."""
    db_path = config.DATABASE_URL.replace('sqlite:///', '')

    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if master_products table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='master_products'
        """)

        if not cursor.fetchone():
            print("Creating master_products table...")
            cursor.execute("""
                CREATE TABLE master_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_name VARCHAR(500) NOT NULL,
                    brand VARCHAR(100),
                    model VARCHAR(200),
                    category VARCHAR(100),
                    normalized_name VARCHAR(500) NOT NULL,
                    search_tokens TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX idx_master_brand ON master_products(brand)")
            cursor.execute("CREATE INDEX idx_master_model ON master_products(model)")
            cursor.execute("CREATE INDEX idx_master_category ON master_products(category)")
            cursor.execute("CREATE INDEX idx_master_normalized ON master_products(normalized_name)")

            print("[OK] Created master_products table")
        else:
            print("[SKIP] master_products table already exists")

        # Check if master_product_id column exists in products table
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'master_product_id' not in columns:
            print("Adding master_product_id column to products table...")
            cursor.execute("""
                ALTER TABLE products
                ADD COLUMN master_product_id INTEGER
            """)

            # Create index
            cursor.execute("CREATE INDEX idx_products_master ON products(master_product_id)")

            print("[OK] Added master_product_id column")
        else:
            print("[SKIP] master_product_id column already exists")

        conn.commit()
        print("\n[OK] Database migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()
