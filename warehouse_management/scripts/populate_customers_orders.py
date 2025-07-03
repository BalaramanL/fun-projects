#!/usr/bin/env python
"""
Populate the database with sample customer and order data.

This script adds sample customers and orders to the database for demonstration purposes.
It requires products, warehouses, and inventory to be populated first.
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

# Sample data for customer generation
FIRST_NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Neha", "Raj", "Ananya", 
               "Sanjay", "Meera", "Arjun", "Divya", "Kiran", "Pooja", "Rohan"]
LAST_NAMES = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Joshi", "Reddy", "Nair", 
              "Iyer", "Menon", "Verma", "Shah", "Das", "Rao", "Mishra"]

# Order status options
ORDER_STATUSES = ["Placed", "Processing", "Shipped", "Delivered", "Cancelled"]

# Payment methods
PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Cash on Delivery", "Wallet"]

def generate_phone_number():
    """Generate a random Indian phone number."""
    return f"+91 {random.randint(7000000000, 9999999999)}"

def generate_email(first_name, last_name):
    """Generate a random email address."""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
    return f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"

def get_warehouses_and_pincodes(conn):
    """Get all warehouses and their pincodes from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT warehouse_id, pincode, latitude, longitude FROM warehouses")
    return cursor.fetchall()

def get_products_by_warehouse(conn, warehouse_id):
    """Get all products available in a specific warehouse."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.product_id, p.price 
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE i.warehouse_id = ? AND i.current_stock > 0
    """, (warehouse_id,))
    return cursor.fetchall()

def populate_customers(conn, num_customers=50):
    """Populate the customers table with sample data."""
    logger.info(f"Populating customers table with {num_customers} customers")
    
    cursor = conn.cursor()
    customers = []
    
    # Get warehouse data for location reference
    warehouses = get_warehouses_and_pincodes(conn)
    if not warehouses:
        logger.error("No warehouses found in the database. Please run populate_warehouses.py first.")
        return []
    
    for _ in range(num_customers):
        # Pick a random warehouse for location reference
        warehouse = random.choice(warehouses)
        warehouse_pincode = warehouse[1]
        warehouse_lat = warehouse[2]
        warehouse_lng = warehouse[3]
        
        # Generate customer data
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        customer = {
            "customer_id": str(uuid.uuid4()),
            "name": f"{first_name} {last_name}",
            "email": generate_email(first_name, last_name),
            "phone": generate_phone_number(),
            "address": f"{random.randint(1, 100)}, {random.choice(['Main', 'Cross'])} Road, {random.choice(['Apartment', 'Villa', 'Residency'])}",
            "pincode": warehouse_pincode,
            # Add small random offset to warehouse location
            "latitude": warehouse_lat + random.uniform(-0.01, 0.01),
            "longitude": warehouse_lng + random.uniform(-0.01, 0.01)
        }
        
        customers.append(customer)
    
    # Insert customers into the database
    for customer in customers:
        try:
            cursor.execute("""
                INSERT INTO customers (
                    customer_id, name, email, phone, address, pincode, latitude, longitude
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer["customer_id"], customer["name"], customer["email"], customer["phone"],
                customer["address"], customer["pincode"], customer["latitude"], customer["longitude"]
            ))
        except sqlite3.Error as e:
            logger.error(f"Error inserting customer {customer['name']}: {e}")
    
    conn.commit()
    logger.info(f"Successfully populated {len(customers)} customers")
    return True

def populate_orders(conn, num_orders=200):
    """Populate the orders and order_items tables with sample data."""
    logger.info(f"Populating orders table with {num_orders} orders")
    
    cursor = conn.cursor()
    
    # Get all customers
    cursor.execute("SELECT customer_id, latitude, longitude, pincode FROM customers")
    customers = cursor.fetchall()
    
    if not customers:
        logger.error("No customers found in the database. Please run populate_customers first.")
        return False
    
    # Get all warehouses
    warehouses = get_warehouses_and_pincodes(conn)
    if not warehouses:
        logger.error("No warehouses found in the database. Please run populate_warehouses.py first.")
        return False
    
    orders = []
    order_items = []
    
    # Generate orders
    for _ in range(num_orders):
        # Pick a random customer
        customer = random.choice(customers)
        customer_id = customer[0]
        customer_lat = customer[1]
        customer_lng = customer[2]
        customer_pincode = customer[3]
        
        # Pick the closest warehouse (simplified - just using same pincode)
        warehouse = random.choice([w for w in warehouses if w[1] == customer_pincode]) if random.random() < 0.7 else random.choice(warehouses)
        warehouse_id = warehouse[0]
        
        # Generate a random date within the last 60 days
        days_ago = random.randint(0, 60)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Determine order status based on date
        if days_ago > 7:
            status = "Delivered" if random.random() < 0.9 else random.choice(["Cancelled", "Delivered"])
        elif days_ago > 3:
            status = random.choice(["Delivered", "Shipped", "Processing"])
        elif days_ago > 1:
            status = random.choice(["Processing", "Shipped"])
        else:
            status = random.choice(["Placed", "Processing"])
        
        order_id = str(uuid.uuid4())
        payment_method = random.choice(PAYMENT_METHODS)
        
        order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "warehouse_id": warehouse_id,
            "order_date": order_date,
            "shipping_address": f"Customer Address for {customer_id}",
            "shipping_pincode": customer_pincode,
            "delivery_address": f"Delivery Address for {customer_id}",
            "delivery_latitude": customer_lat,
            "delivery_longitude": customer_lng,
            "status": status,
            "payment_method": payment_method,
            "total_amount": 0
        }
        
        orders.append(order)
        
        # Get products available in the selected warehouse
        products = get_products_by_warehouse(conn, warehouse_id)
        if not products:
            logger.warning(f"No products found for warehouse {warehouse_id}. Skipping order items.")
            continue
        
        # Generate 1-5 order items
        num_items = random.randint(1, 5)
        selected_products = random.sample(products, min(num_items, len(products)))
        
        total_amount = 0
        for product in selected_products:
            product_id = product[0]
            unit_price = product[1]
            quantity = random.randint(1, 5)
            total_price = unit_price * quantity
            total_amount += total_price
            
            order_item = {
                "item_id": str(uuid.uuid4()),
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price
            }
            
            order_items.append(order_item)
        
        # Update order with total amount
        order["total_amount"] = total_amount
    
    # Insert orders into the database
    for order in orders:
        try:
            cursor.execute("""
                INSERT INTO orders (
                    order_id, customer_id, warehouse_id, order_date, shipping_address,
                    shipping_pincode, delivery_address, delivery_latitude, delivery_longitude,
                    total_amount, status, payment_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order["order_id"], order["customer_id"], order["warehouse_id"],
                order["order_date"], order["shipping_address"], order["shipping_pincode"],
                order["delivery_address"], order["delivery_latitude"], order["delivery_longitude"],
                order["total_amount"], order["status"], order["payment_method"]
            ))
        except sqlite3.Error as e:
            logger.error(f"Error inserting order {order['order_id']}: {e}")
    
    # Insert order items into the database
    for item in order_items:
        try:
            cursor.execute("""
                INSERT INTO order_items (
                    item_id, order_id, product_id, quantity, unit_price, total_price
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item["item_id"], item["order_id"], item["product_id"], item["quantity"],
                item["unit_price"], item["total_price"]
            ))
        except sqlite3.Error as e:
            logger.error(f"Error inserting order item for order {item['order_id']}: {e}")
    
    conn.commit()
    logger.info(f"Successfully populated {len(orders)} orders with {len(order_items)} order items")
    return True

def main():
    """Main function to populate customers and orders."""
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
        # Populate customers
        success_customers = populate_customers(conn)
        if not success_customers:
            logger.error("Customer population failed")
            return 1
        
        # Populate orders
        success_orders = populate_orders(conn)
        if success_orders:
            logger.info("Customer and order population completed successfully")
            return 0
        else:
            logger.error("Order population failed")
            return 1
    except Exception as e:
        logger.error(f"Error populating customers and orders: {str(e)}", exc_info=True)
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
