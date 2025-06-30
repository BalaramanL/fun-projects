#!/usr/bin/env python
"""
Populate the database with sample product data.

This script adds sample products to the database for demonstration purposes.
"""
import os
import sys
import logging
import sqlite3
import random
import uuid
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Sample data for products
PRODUCT_CATEGORIES = [
    "Groceries", "Fresh Produce", "Dairy", "Bakery", "Beverages", 
    "Snacks", "Household", "Personal Care"
]

PRODUCT_SUBCATEGORIES = {
    "Groceries": ["Rice", "Flour", "Oil", "Spices", "Pasta", "Canned Goods"],
    "Fresh Produce": ["Vegetables", "Fruits", "Herbs"],
    "Dairy": ["Milk", "Cheese", "Yogurt", "Butter", "Eggs"],
    "Bakery": ["Bread", "Cakes", "Cookies", "Pastries"],
    "Beverages": ["Water", "Soda", "Juice", "Tea", "Coffee"],
    "Snacks": ["Chips", "Nuts", "Chocolates", "Candy"],
    "Household": ["Cleaning", "Laundry", "Paper Goods"],
    "Personal Care": ["Soap", "Shampoo", "Dental", "Skincare"]
}

BRANDS = [
    "FreshFarms", "NatureBest", "GreenGrocer", "HealthyHarvest", 
    "OrganicOrigins", "PurePantry", "EcoEssentials", "VitalVeggies",
    "DairyDelight", "BakeryBliss", "CleanCare", "FreshSip"
]

def generate_product_name(subcategory):
    """Generate a random product name based on subcategory."""
    adjectives = ["Fresh", "Organic", "Premium", "Natural", "Classic", "Homestyle", "Gourmet"]
    return f"{random.choice(adjectives)} {subcategory} {random.choice(['Pack', 'Selection', 'Item', 'Product'])}"

def populate_products(conn, num_products=100):
    """Populate the products table with sample data."""
    logger.info(f"Populating products table with {num_products} products")
    
    cursor = conn.cursor()
    products = []
    
    for _ in range(num_products):
        category = random.choice(PRODUCT_CATEGORIES)
        subcategory = random.choice(PRODUCT_SUBCATEGORIES.get(category, ["General"]))
        brand = random.choice(BRANDS)
        name = generate_product_name(subcategory)
        
        product = {
            "product_id": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "subcategory": subcategory,
            "brand": brand,
            "price": round(random.uniform(10, 1000), 2),  # Price in rupees
            "weight_grams": random.randint(50, 5000) if random.random() > 0.3 else None,
            "volume_ml": random.randint(100, 3000) if random.random() > 0.7 else None,
            "shelf_life_days": random.randint(1, 365),
            "requires_refrigeration": 1 if category in ["Dairy", "Fresh Produce"] and random.random() > 0.5 else 0
        }
        
        products.append(product)
    
    # Insert products into the database
    for product in products:
        try:
            cursor.execute("""
                INSERT INTO products (
                    product_id, name, category, subcategory, brand, price, 
                    weight_grams, volume_ml, shelf_life_days, requires_refrigeration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product["product_id"], product["name"], product["category"], 
                product["subcategory"], product["brand"], product["price"],
                product["weight_grams"], product["volume_ml"], 
                product["shelf_life_days"], product["requires_refrigeration"]
            ))
        except sqlite3.Error as e:
            logger.error(f"Error inserting product {product['name']}: {e}")
    
    conn.commit()
    logger.info(f"Successfully populated {num_products} products")
    return products

def main():
    """Main function to populate products."""
    # Default database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'warehouse.db')
    
    # Allow custom database path from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}. Please run setup_database.py first.")
        return 1
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    
    try:
        # Populate products
        populate_products(conn)
        logger.info("Product population completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Error populating products: {str(e)}", exc_info=True)
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
