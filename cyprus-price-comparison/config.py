"""Configuration settings for the price comparison pipeline."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
CACHE_DIR = Path(os.getenv("CACHE_DIR", "./cache"))
CACHE_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///products.db")

# Rate limiting
RATE_LIMIT_PER_DOMAIN = float(os.getenv("RATE_LIMIT_PER_DOMAIN", "1.0"))

# Scraper settings
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
TIMEOUT = int(os.getenv("TIMEOUT", "30000"))
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"

# Target stores
STORES = {
    "public": {
        "name": "Public Cyprus",
        "base_url": "https://www.public.cy/",
        "categories": [
            "electronics",
            "smartphones",
            "laptops",
            "televisions",
            "gaming"
        ]
    },
    "stephanis": {
        "name": "Stephanis",
        "base_url": "https://www.stephanis.com.cy/",
        "categories": [
            "smartphones",
            "televisions",
            "laptops",
            "gaming"
        ]
    }
}
