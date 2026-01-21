"""Flask web application for Cyprus Price Comparison."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request, jsonify
from models import Product, MasterProduct, MasterProductVariant, get_session
from search_products import search_products, get_best_deals, get_product_by_master_id, get_product_by_variant_id
from product_matcher import ProductMatcher
from sqlalchemy import func, desc

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


@app.route('/')
def index():
    """Home page with search."""
    session = get_session()
    try:
        # Get statistics
        total_products = session.query(Product).count()
        total_masters = session.query(MasterProduct).count()
        stores = session.query(Product.store).distinct().count()

        # Get featured products (products with biggest discounts)
        featured = session.query(Product).filter(
            Product.discount_percentage.isnot(None),
            Product.discount_percentage > 0
        ).order_by(desc(Product.discount_percentage)).limit(6).all()

        featured_products = []
        for product in featured:
            featured_products.append({
                'id': product.id,
                'master_id': product.master_product_id,
                'name': product.name,
                'store': product.store,
                'price': product.price,
                'original_price': product.original_price,
                'discount_percentage': product.discount_percentage,
                'image_url': product.image_url,
                'url': product.url
            })

        stats = {
            'total_products': total_products,
            'unique_products': total_masters,
            'stores': stores
        }

        return render_template('index.html', stats=stats, featured=featured_products)
    finally:
        session.close()


@app.route('/search')
def search():
    """Search results page."""
    query = request.args.get('q', '')

    if not query:
        return render_template('search.html', results=[], query='')

    results = search_products(query, limit=50)

    return render_template('search.html', results=results, query=query)


@app.route('/product/<int:master_id>')
def product_detail(master_id):
    """Product detail page showing all variants for a master product."""
    session = get_session()
    try:
        master = session.query(MasterProduct).filter(
            MasterProduct.id == master_id
        ).first()

        if not master:
            return render_template('error.html',
                                 error='Product not found'), 404

        variants = session.query(MasterProductVariant).filter(
            MasterProductVariant.master_product_id == master_id
        ).all()

        if not variants:
            products = session.query(Product).filter(
                Product.master_product_id == master_id
            ).all()

            if not products:
                return render_template('error.html',
                                     error='No store listings found'), 404

            # Calculate price statistics
            prices = [p.price for p in products if p.price > 0]
            cheapest_price = min(prices) if prices else 0
            most_expensive = max(prices) if prices else 0
            avg_price = sum(prices) / len(prices) if prices else 0

            stores_data = []
            for product in products:
                stores_data.append({
                    'store': product.store,
                    'name': product.name,
                    'price': product.price,
                    'original_price': product.original_price,
                    'discount_percentage': product.discount_percentage,
                    'availability': product.availability,
                    'url': product.url,
                    'image_url': product.image_url
                })

            stores_data.sort(key=lambda x: x['price'])

            product_data = {
                'master_id': master.id,
                'canonical_name': master.canonical_name,
                'brand': master.brand,
                'model': master.model,
                'category': master.category,
                'cheapest_price': cheapest_price,
                'most_expensive': most_expensive,
                'avg_price': avg_price,
                'price_difference': most_expensive - cheapest_price,
                'stores': stores_data
            }

            return render_template('product.html', product=product_data)

        variants_data = []
        for variant in variants:
            products = session.query(Product).filter(
                Product.variant_id == variant.id
            ).all()
            if not products:
                continue
            prices = [p.price for p in products if p.price > 0]
            cheapest_price = min(prices) if prices else 0
            most_expensive = max(prices) if prices else 0
            variants_data.append({
                'variant_id': variant.id,
                'capacity': variant.capacity,
                'cheapest_price': cheapest_price,
                'most_expensive': most_expensive,
                'store_count': len(products),
                'image_url': products[0].image_url if products else None
            })

        product_data = {
            'master_id': master.id,
            'canonical_name': master.canonical_name,
            'brand': master.brand,
            'model': master.model,
            'category': master.category,
            'variants': variants_data
        }

        return render_template('product.html', product=product_data)
    finally:
        session.close()


@app.route('/variant/<int:variant_id>')
def variant_detail(variant_id):
    """Variant detail page showing store comparisons."""
    session = get_session()
    try:
        variant = session.query(MasterProductVariant).filter(
            MasterProductVariant.id == variant_id
        ).first()

        if not variant:
            return render_template('error.html',
                                 error='Variant not found'), 404

        master = session.query(MasterProduct).filter(
            MasterProduct.id == variant.master_product_id
        ).first()

        if not master:
            return render_template('error.html',
                                 error='Product not found'), 404

        products = session.query(Product).filter(
            Product.variant_id == variant_id
        ).all()

        if not products:
            return render_template('error.html',
                                 error='No store listings found'), 404

        prices = [p.price for p in products if p.price > 0]
        cheapest_price = min(prices) if prices else 0
        most_expensive = max(prices) if prices else 0
        avg_price = sum(prices) / len(prices) if prices else 0

        stores_data = []
        for product in products:
            stores_data.append({
                'store': product.store,
                'name': product.name,
                'price': product.price,
                'original_price': product.original_price,
                'discount_percentage': product.discount_percentage,
                'availability': product.availability,
                'url': product.url,
                'image_url': product.image_url
            })

        stores_data.sort(key=lambda x: x['price'])

        product_data = {
            'variant_id': variant.id,
            'master_id': master.id,
            'canonical_name': master.canonical_name,
            'brand': master.brand,
            'model': master.model,
            'category': master.category,
            'capacity': variant.capacity,
            'cheapest_price': cheapest_price,
            'most_expensive': most_expensive,
            'avg_price': avg_price,
            'price_difference': most_expensive - cheapest_price,
            'stores': stores_data
        }

        return render_template('product.html', product=product_data)
    finally:
        session.close()


@app.route('/deals')
def deals():
    """Best deals page."""
    store = request.args.get('store')
    deals = get_best_deals(store=store, limit=30)

    session = get_session()
    try:
        stores = session.query(Product.store).distinct().all()
        store_list = [s[0] for s in stores]

        return render_template('deals.html', deals=deals,
                             stores=store_list, selected_store=store)
    finally:
        session.close()


@app.route('/browse')
def browse():
    """Browse all products by category/brand."""
    category = request.args.get('category')
    brand = request.args.get('brand')
    page = int(request.args.get('page', 1))
    per_page = 24

    session = get_session()
    try:
        # Get filter options
        categories = session.query(MasterProduct.category).filter(
            MasterProduct.category.isnot(None),
            MasterProduct.category != ''
        ).distinct().all()
        category_list = sorted([c[0] for c in categories])

        brands = session.query(MasterProduct.brand).filter(
            MasterProduct.brand.isnot(None),
            MasterProduct.brand != ''
        ).distinct().all()
        brand_list = sorted([b[0] for b in brands])

        # Build query
        query = session.query(MasterProduct)

        if category:
            query = query.filter(MasterProduct.category == category)

        if brand:
            query = query.filter(MasterProduct.brand == brand)

        # Get total count
        total = query.count()
        total_pages = (total + per_page - 1) // per_page

        # Get paginated results
        masters = query.order_by(MasterProduct.canonical_name).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        # Get product data with prices
        products_data = []
        for master in masters:
            products = session.query(Product).filter(
                Product.master_product_id == master.id
            ).all()

            if products:
                prices = [p.price for p in products if p.price > 0]
                cheapest = min(prices) if prices else 0

                # Get image from first product
                image_url = products[0].image_url if products else None

                products_data.append({
                    'master_id': master.id,
                    'name': master.canonical_name,
                    'brand': master.brand,
                    'category': master.category,
                    'cheapest_price': cheapest,
                    'store_count': len(products),
                    'image_url': image_url
                })

        return render_template('browse.html',
                             products=products_data,
                             categories=category_list,
                             brands=brand_list,
                             selected_category=category,
                             selected_brand=brand,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    finally:
        session.close()


# API Endpoints

@app.route('/api/search')
def api_search():
    """API endpoint for product search."""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))

    if not query:
        return jsonify({'error': 'Query parameter required'}), 400

    results = search_products(query, limit=limit)
    return jsonify(results)


@app.route('/api/product/<int:master_id>')
def api_product(master_id):
    """API endpoint for product details (master + variants)."""
    product = get_product_by_master_id(master_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify(product)


@app.route('/api/variant/<int:variant_id>')
def api_variant(variant_id):
    """API endpoint for variant details."""
    product = get_product_by_variant_id(variant_id)

    if not product:
        return jsonify({'error': 'Variant not found'}), 404

    return jsonify(product)


@app.route('/api/deals')
def api_deals():
    """API endpoint for best deals."""
    store = request.args.get('store')
    limit = int(request.args.get('limit', 10))

    deals = get_best_deals(store=store, limit=limit)
    return jsonify(deals)


@app.route('/api/stats')
def api_stats():
    """API endpoint for database statistics."""
    session = get_session()
    try:
        total_products = session.query(Product).count()
        total_masters = session.query(MasterProduct).count()

        stores = session.query(
            Product.store,
            func.count(Product.id).label('count')
        ).group_by(Product.store).all()

        store_stats = {store: count for store, count in stores}

        return jsonify({
            'total_products': total_products,
            'unique_products': total_masters,
            'stores': store_stats,
            'avg_products_per_master': round(total_products / total_masters, 2) if total_masters > 0 else 0
        })
    finally:
        session.close()


if __name__ == '__main__':
    import os

    print("\n" + "="*60)
    print("CYPRUS PRICE COMPARISON WEB APP")
    print("="*60)
    print("\nStarting web server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    # Use environment variable for debug mode (default: False for security)
    # Set FLASK_DEBUG=1 for development, but NEVER in production
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')

    # Only bind to 0.0.0.0 if explicitly requested (production use)
    # Default to 127.0.0.1 (localhost only) for security
    host = os.getenv('FLASK_HOST', '127.0.0.1')

    if debug_mode:
        print("[WARNING] Debug mode is enabled! This is UNSAFE for production.")
    if host == '0.0.0.0':
        print(f"[WARNING] Binding to {host} - server is accessible from network!")

    app.run(debug=debug_mode, host=host, port=5000)
