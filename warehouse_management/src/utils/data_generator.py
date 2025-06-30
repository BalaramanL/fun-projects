"""
Data generator utility for the warehouse management system.
Provides functions to generate realistic sample data.
"""
import random
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta, time

import numpy as np
from sqlalchemy.orm import Session

from src.config.constants import (
    WAREHOUSE_AREAS, WAREHOUSE_COORDINATES, 
    PRODUCT_CATEGORIES, UNIT_TYPES, SHELF_LIFE_RANGES,
    PRICE_RANGES, HOURLY_DEMAND_PATTERNS, DAILY_DEMAND_PATTERNS,
    MONTHLY_DEMAND_PATTERNS, BANGALORE_BOUNDS
)
from src.models.product import Product
from src.models.warehouse import Warehouse
from src.models.inventory import Inventory
from src.models.events import PurchaseEvent, PincodeMapping

logger = logging.getLogger(__name__)

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

def generate_product_name(category: str, subcategory: str) -> str:
    """
    Generate a realistic product name based on category and subcategory.
    
    Args:
        category: Product category
        subcategory: Product subcategory
        
    Returns:
        Generated product name
    """
    # Common adjectives for products
    adjectives = ["Fresh", "Premium", "Organic", "Natural", "Classic", "Special", 
                 "Homestyle", "Traditional", "Gourmet", "Deluxe", "Everyday", 
                 "Select", "Choice", "Signature", "Essential"]
    
    # Common product names by subcategory
    product_names = {
        "Vegetables": ["Tomatoes", "Onions", "Potatoes", "Carrots", "Spinach", 
                      "Cucumber", "Capsicum", "Broccoli", "Cauliflower", "Beans",
                      "Peas", "Cabbage", "Okra", "Eggplant", "Zucchini"],
        "Fruits": ["Apples", "Bananas", "Oranges", "Grapes", "Watermelon", 
                  "Mango", "Pineapple", "Papaya", "Pomegranate", "Kiwi",
                  "Strawberries", "Guava", "Pear", "Plum", "Cherries"],
        "Dairy": ["Milk", "Curd", "Paneer", "Cheese", "Butter", 
                 "Ghee", "Cream", "Yogurt", "Buttermilk", "Lassi"],
        "Meat & Seafood": ["Chicken", "Mutton", "Fish", "Prawns", "Eggs", 
                          "Crab", "Sausages", "Salami", "Ham", "Bacon"],
        "Snacks": ["Chips", "Biscuits", "Namkeen", "Popcorn", "Chocolate", 
                  "Candy", "Cookies", "Wafers", "Nuts", "Trail Mix"],
        "Beverages": ["Water", "Soda", "Juice", "Tea", "Coffee", 
                     "Energy Drink", "Soft Drink", "Milk Shake", "Smoothie", "Lassi"],
        "Personal Care": ["Soap", "Shampoo", "Toothpaste", "Face Wash", "Body Lotion", 
                         "Deodorant", "Hand Wash", "Sanitizer", "Shower Gel", "Conditioner"],
        "Breakfast & Dairy": ["Bread", "Cereal", "Jam", "Honey", "Butter", 
                             "Cheese Spread", "Peanut Butter", "Oats", "Cornflakes", "Muesli"],
        "Instant Food": ["Noodles", "Pasta", "Soup", "Ready Meals", "Frozen Food", 
                        "Canned Food", "Instant Mix", "Curry Paste", "Sauce", "Seasoning"],
        "Household": ["Detergent", "Dishwash", "Floor Cleaner", "Toilet Cleaner", "Air Freshener", 
                     "Mosquito Repellent", "Tissue Paper", "Kitchen Towel", "Garbage Bags", "Cleaning Cloth"],
        "Baby Care": ["Diapers", "Baby Food", "Baby Wipes", "Baby Soap", "Baby Shampoo", 
                     "Baby Lotion", "Baby Powder", "Baby Oil", "Baby Cream", "Baby Wash"],
        "Pet Care": ["Pet Food", "Pet Treats", "Pet Shampoo", "Pet Toys", "Pet Accessories", 
                    "Pet Litter", "Pet Grooming Kit", "Pet Bed", "Pet Bowl", "Pet Leash"],
        "Ready-to-Cook": ["Curry Mix", "Spice Mix", "Batter", "Marinade", "Sauce Mix", 
                         "Cake Mix", "Pizza Base", "Pasta Sauce", "Soup Mix", "Dessert Mix"],
        "Staples": ["Rice", "Wheat Flour", "Pulses", "Sugar", "Salt", 
                   "Cooking Oil", "Spices", "Masalas", "Dry Fruits", "Grains"]
    }
    
    # Get product names for the subcategory
    names = product_names.get(subcategory, ["Item"])
    
    # Generate a product name
    if random.random() < 0.7:  # 70% chance to include an adjective
        adjective = random.choice(adjectives)
        name = random.choice(names)
        brand = generate_brand_name()
        return f"{brand} {adjective} {name}"
    else:
        name = random.choice(names)
        brand = generate_brand_name()
        return f"{brand} {name}"

def generate_brand_name() -> str:
    """
    Generate a random brand name.
    
    Returns:
        Generated brand name
    """
    prefixes = ["Sun", "Moon", "Star", "Earth", "Sky", "Ocean", "Mountain", "River", 
               "Forest", "Garden", "Field", "Valley", "Dawn", "Dusk", "Twilight",
               "Royal", "Golden", "Silver", "Diamond", "Crystal", "Emerald", "Ruby",
               "Fresh", "Pure", "Natural", "Organic", "Green", "Blue", "Red", "Yellow"]
    
    suffixes = ["Farm", "Foods", "Harvest", "Produce", "Organics", "Naturals", "Fresh",
               "Delights", "Treats", "Essentials", "Basics", "Premium", "Select", "Choice",
               "Kitchen", "Pantry", "Garden", "Orchard", "Valley", "Hills", "Fields"]
    
    # 20% chance for a single word brand name
    if random.random() < 0.2:
        return random.choice(prefixes)
    
    # 80% chance for a two-word brand name
    return f"{random.choice(prefixes)}{random.choice(suffixes)}"

def generate_products(count: int = 250) -> List[Dict[str, Any]]:
    """
    Generate a list of realistic grocery products.
    
    Args:
        count: Number of products to generate
        
    Returns:
        List of product dictionaries
    """
    products = []
    
    for _ in range(count):
        # Select random category and subcategory
        category = random.choice(list(PRODUCT_CATEGORIES.keys()))
        subcategory = random.choice(PRODUCT_CATEGORIES[category])
        
        # Generate product name
        name = generate_product_name(category, subcategory)
        
        # Generate price within range for the subcategory
        min_price, max_price = PRICE_RANGES.get(subcategory, (10, 500))
        price = round(random.uniform(min_price, max_price), 2)
        
        # Select random unit type
        unit_type = random.choice(UNIT_TYPES)
        
        # Generate shelf life within range for the subcategory
        min_shelf_life, max_shelf_life = SHELF_LIFE_RANGES.get(subcategory, (30, 365))
        shelf_life_days = random.randint(min_shelf_life, max_shelf_life)
        
        # Generate creation date (within last year)
        days_ago = random.randint(0, 365)
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        # Create product dictionary
        product = {
            "id": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "subcategory": subcategory,
            "price": price,
            "unit_type": unit_type,
            "shelf_life_days": shelf_life_days,
            "created_at": created_at
        }
        
        products.append(product)
    
    return products

def generate_warehouses() -> List[Dict[str, Any]]:
    """
    Generate warehouses in Bangalore locations.
    
    Returns:
        List of warehouse dictionaries
    """
    warehouses = []
    
    for area in WAREHOUSE_AREAS:
        # Get coordinates for the area
        latitude, longitude = WAREHOUSE_COORDINATES.get(area, (0, 0))
        
        # Add some randomness to coordinates (within 500m)
        latitude += random.uniform(-0.002, 0.002)
        longitude += random.uniform(-0.002, 0.002)
        
        # Generate capacity based on area (larger for central areas)
        if area in ["Koramangala", "Indiranagar", "Jayanagar"]:
            capacity = random.randint(5000, 8000)  # larger warehouses
        else:
            capacity = random.randint(3000, 5000)  # smaller warehouses
        
        # Generate staff count based on capacity
        staff_ratio = random.uniform(0.01, 0.015)  # 1-1.5 staff per 100 cubic meters
        current_staff = int(capacity * staff_ratio)
        
        # Generate operational hours
        opening_hour = random.randint(6, 9)  # 6 AM to 9 AM
        closing_hour = random.randint(19, 22)  # 7 PM to 10 PM
        opening_time = time(opening_hour, 0)
        closing_time = time(closing_hour, 0)
        
        # Create warehouse dictionary
        warehouse = {
            "id": str(uuid.uuid4()),
            "name": f"{area} Fulfillment Center",
            "area": area,
            "latitude": latitude,
            "longitude": longitude,
            "capacity": capacity,
            "current_staff": current_staff,
            "opening_time": opening_time,
            "closing_time": closing_time
        }
        
        warehouses.append(warehouse)
    
    return warehouses

# More functions will be implemented in helper modules
