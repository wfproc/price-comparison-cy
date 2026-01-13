# Cyprus Price Comparison - Web Application

A beautiful, modern web interface for comparing electronics prices across Cyprus stores.

## Features

### 🏠 **Home Page**
- Hero search bar with auto-focus
- Statistics dashboard (products, stores, listings)
- Featured deals carousel
- "How It Works" section

### 🔍 **Search**
- Full-text product search
- Shows all store variants for each product
- Price range display
- Savings calculator
- "Cheapest" badge highlighting
- Direct links to buy

### 📱 **Product Detail Page**
- Complete price comparison across all stores
- Price statistics (cheapest, average, highest)
- Savings calculator
- Availability status per store
- Product images
- Buy buttons for each store

### 🏷️ **Best Deals**
- Products with biggest discounts
- Filter by store
- Discount percentage badges
- Original vs current price
- Savings amount

### 📚 **Browse**
- Filter by category
- Filter by brand
- Pagination (24 products per page)
- Grid view with images
- "From €X" pricing
- Store count per product

### 🔌 **REST API**
All features available via JSON API:
- `GET /api/search?q=iphone&limit=20`
- `GET /api/product/<master_id>`
- `GET /api/deals?store=public&limit=10`
- `GET /api/stats`

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Flask 2.2.5 is now included in requirements.

### 2. Ensure Database is Set Up

```bash
# If you haven't already
python migrate_db.py
```

### 3. Run the Web Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

---

## Usage

### Starting the Server

```bash
python app.py
```

Output:
```
============================================================
CYPRUS PRICE COMPARISON WEB APP
============================================================

Starting web server...
Open your browser to: http://localhost:5000

Press Ctrl+C to stop the server
============================================================
```

### Accessing the Application

**Web Interface:**
- Home: `http://localhost:5000/`
- Search: `http://localhost:5000/search?q=iphone`
- Product: `http://localhost:5000/product/1`
- Browse: `http://localhost:5000/browse`
- Deals: `http://localhost:5000/deals`

**API Endpoints:**
- Search: `http://localhost:5000/api/search?q=ipad&limit=10`
- Product: `http://localhost:5000/api/product/1`
- Deals: `http://localhost:5000/api/deals?store=public`
- Stats: `http://localhost:5000/api/stats`

---

## Pages Overview

### Home Page (`/`)
- Search bar
- Statistics (unique products, stores, listings)
- Featured deals (top 6 discounted products)
- How it works section
- Responsive design

### Search Results (`/search?q=<query>`)
- Query results with relevance ranking
- Product cards showing:
  - Canonical name
  - Brand badge
  - Model info
  - Price range
  - Savings amount
  - Store availability
  - Cheapest store highlighted
- Direct buy links

### Product Detail (`/product/<master_id>`)
- Comprehensive product information
- Price statistics box
- Store comparison table
- Availability per store
- Savings calculator
- Buy buttons
- Product images

### Browse (`/browse`)
- Category filter dropdown
- Brand filter dropdown
- Pagination (24 per page)
- Product grid
- "From €X" pricing
- Store count

### Deals (`/deals`)
- Store filter
- Discount percentage badges
- Original vs current price
- Savings amount
- Sorted by discount percentage

---

## Design Features

### Responsive Design
- Mobile-first approach
- Works on phones, tablets, desktops
- Collapsible navigation on mobile
- Grid layouts adapt to screen size

### Color Scheme
- Primary: Blue (#2563eb)
- Success: Green (#10b981)
- Danger: Red (#ef4444)
- Warning: Orange (#f59e0b)
- Clean white/gray backgrounds

### UI Components
- Modern card-based design
- Shadow elevations
- Hover effects
- Smooth transitions
- Loading states
- Badge indicators
- Status chips

### Accessibility
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus indicators
- Alt text for images
- Color contrast compliance

---

## API Documentation

### Search Products

```http
GET /api/search?q=<query>&limit=<number>
```

**Parameters:**
- `q` (required): Search query
- `limit` (optional): Max results (default: 20)

**Response:**
```json
[
  {
    "master_id": 1,
    "name": "Apple iPhone 16 Pro 128GB",
    "brand": "apple",
    "model": "iphone 16 pro",
    "cheapest_price": 1299.00,
    "most_expensive": 1349.00,
    "price_difference": 50.00,
    "store_count": 2,
    "stores": [
      {
        "store": "public",
        "price": 1299.00,
        "url": "https://...",
        "availability": "in_stock"
      }
    ]
  }
]
```

### Get Product Details

```http
GET /api/product/<master_id>
```

**Response:**
```json
{
  "master_id": 1,
  "name": "Apple iPhone 16 Pro 128GB",
  "brand": "apple",
  "model": "iphone 16 pro",
  "stores": [
    {
      "store": "public",
      "price": 1299.00,
      "url": "https://...",
      "name": "Smartphone APPLE iPhone 16 Pro..."
    }
  ]
}
```

### Get Best Deals

```http
GET /api/deals?store=<store_name>&limit=<number>
```

**Parameters:**
- `store` (optional): Filter by store
- `limit` (optional): Max results (default: 10)

**Response:**
```json
[
  {
    "store": "public",
    "name": "Samsung Galaxy S24",
    "price": 799.00,
    "original_price": 999.00,
    "discount_percentage": 20.0,
    "savings": 200.00,
    "url": "https://..."
  }
]
```

### Get Statistics

```http
GET /api/stats
```

**Response:**
```json
{
  "total_products": 231,
  "unique_products": 173,
  "stores": {
    "public": 114,
    "stephanis": 117
  },
  "avg_products_per_master": 1.34
}
```

---

## Customization

### Changing Colors

Edit `static/css/style.css`:

```css
:root {
    --primary-color: #2563eb;  /* Change this */
    --success-color: #10b981;
    --danger-color: #ef4444;
    /* ... */
}
```

### Adding a New Store

1. Create scraper in `scrapers/`
2. Add to `main.py`
3. Run `python main.py`
4. Store automatically appears in filters and comparisons

No changes to web app needed!

### Changing Products Per Page

In `app.py`, line ~93:

```python
per_page = 24  # Change this number
```

### Changing Featured Products Count

In `app.py`, line ~26:

```python
.limit(6)  # Change from 6 to your preferred number
```

---

## Deployment

### Production Deployment

**Option 1: Gunicorn (Linux)**

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Option 2: Waitress (Windows/Linux)**

```bash
pip install waitress
waitress-serve --port=5000 app:app
```

**Option 3: Docker**

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t cyprus-prices .
docker run -p 5000:5000 cyprus-prices
```

### Environment Variables

Create `.env` file:

```env
DATABASE_URL=sqlite:///products.db
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/cyprus-price-comparison/static;
    }
}
```

---

## Performance

### Current Performance
- Page load: < 1 second
- Search: < 500ms (231 products)
- API response: < 200ms

### Optimization Tips

1. **Enable caching** (Flask-Caching):
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)  # 5 minutes
def expensive_function():
    pass
```

2. **Add database indexes** (already included)

3. **Use CDN** for static files

4. **Enable gzip compression**:
```python
from flask_compress import Compress
Compress(app)
```

---

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
python app.py
# Then edit app.py line ~260:
app.run(debug=True, host='0.0.0.0', port=8000)
```

### Database Not Found

```bash
# Run migration
python migrate_db.py

# Or create fresh database
python main.py
```

### Static Files Not Loading

Check that these directories exist:
```
static/
├── css/
│   └── style.css
└── js/
    └── main.js
```

### No Products Showing

```bash
# Scrape products
python main.py

# Run matching
python product_matcher.py
```

---

## Screenshots

### Home Page
- Hero with search
- Statistics dashboard
- Featured deals grid

### Search Results
- Product cards
- Price comparison
- Cheapest highlighting

### Product Detail
- Full comparison table
- Price statistics
- Store availability

### Browse
- Filter by category/brand
- Pagination
- Grid view

### Deals
- Discount badges
- Savings calculator
- Store filter

---

## Technology Stack

**Backend:**
- Flask 2.2.5 (Python web framework)
- SQLAlchemy 2.0 (ORM)
- SQLite (Database)

**Frontend:**
- HTML5 (Semantic markup)
- CSS3 (Custom styling, no frameworks)
- Vanilla JavaScript (No dependencies)

**Features:**
- Responsive design
- REST API
- Product matching system
- Price comparison engine

---

## Next Steps

### Potential Enhancements

1. **User Accounts**
   - Save favorite products
   - Price drop alerts
   - Wishlist

2. **Price History**
   - Charts showing price trends
   - Historical data analysis
   - Best time to buy

3. **Advanced Filters**
   - Price range slider
   - Availability filter
   - Store selection

4. **Social Features**
   - Share deals
   - Product reviews
   - Rating system

5. **Mobile App**
   - React Native
   - Push notifications
   - Barcode scanner

6. **Analytics**
   - Popular products
   - Search trends
   - User behavior

---

## License

MIT License - Feel free to use and modify!

## Support

For issues or questions:
- Check the troubleshooting section
- Review the API documentation
- Check the main README.md

---

**Enjoy comparing prices! 🎉**
