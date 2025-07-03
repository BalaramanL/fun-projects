#!/usr/bin/env python
"""
Simulate live user purchase events for the warehouse management system.

This script runs in a separate thread and continuously generates purchase events
to simulate real-time activity in the system.
"""
import os
import sys
import time
import logging
import sqlite3
import random
import uuid
import threading
import signal
from datetime import datetime
from queue import Queue

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global flag to control the simulation
running = True
event_queue = Queue()

class LiveEventSimulator:
    """Simulates live purchase events in the warehouse management system."""
    
    def __init__(self, db_path, events_per_minute=10):
        """Initialize the simulator with database path and event rate."""
        self.db_path = db_path
        self.events_per_minute = events_per_minute
        self.sleep_time = 60.0 / events_per_minute if events_per_minute > 0 else 6.0
        self.customers = []
        self.warehouses = []
        self.products = []
        self.event_count = 0
        
    def load_data(self):
        """Load necessary data from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Load customers
            cursor.execute("SELECT customer_id, latitude, longitude, pincode FROM customers")
            self.customers = cursor.fetchall()
            
            # Load warehouses
            cursor.execute("SELECT warehouse_id, pincode, latitude, longitude FROM warehouses")
            self.warehouses = cursor.fetchall()
            
            # Load products with inventory
            cursor.execute("""
                SELECT p.product_id, p.price, i.warehouse_id
                FROM products p
                JOIN inventory i ON p.product_id = i.product_id
                WHERE i.current_stock > 0
            """)
            self.products = cursor.fetchall()
            
            if not self.customers or not self.warehouses or not self.products:
                logger.error("Missing data in the database. Make sure to run the population scripts first.")
                return False
                
            logger.info(f"Loaded {len(self.customers)} customers, {len(self.warehouses)} warehouses, and {len(self.products)} products with inventory")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error loading data from database: {e}")
            return False
        finally:
            conn.close()
    
    def generate_event(self):
        """Generate a single purchase event."""
        if not self.customers or not self.warehouses or not self.products:
            logger.error("No data available to generate events")
            return None
        
        # Pick a random customer
        customer = random.choice(self.customers)
        customer_id = customer[0]
        customer_pincode = customer[3]
        
        # Pick a warehouse (prefer one in the same pincode)
        matching_warehouses = [w for w in self.warehouses if w[1] == customer_pincode]
        warehouse = random.choice(matching_warehouses) if matching_warehouses else random.choice(self.warehouses)
        warehouse_id = warehouse[0]
        
        # Get products available in this warehouse
        warehouse_products = [p for p in self.products if p[2] == warehouse_id]
        if not warehouse_products:
            logger.warning(f"No products available in warehouse {warehouse_id}")
            return None
        
        # Generate 1-3 order items
        num_items = random.randint(1, 3)
        selected_products = random.sample(warehouse_products, min(num_items, len(warehouse_products)))
        
        order_id = str(uuid.uuid4())
        order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "Placed"
        payment_method = random.choice(["Credit Card", "Debit Card", "UPI", "Cash on Delivery", "Wallet"])
        
        total_amount = 0
        order_items = []
        
        for product in selected_products:
            product_id = product[0]
            unit_price = product[1]
            quantity = random.randint(1, 3)
            total_price = unit_price * quantity
            total_amount += total_price
            
            order_items.append({
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price
            })
        
        event = {
            "order": {
                "order_id": order_id,
                "customer_id": customer_id,
                "warehouse_id": warehouse_id,
                "order_date": order_date,
                "total_amount": total_amount,
                "status": status,
                "payment_method": payment_method
            },
            "order_items": order_items
        }
        
        return event
    
    def save_event(self, event):
        """Save the generated event to the database."""
        if not event:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get customer data for delivery details
            cursor.execute("""
                SELECT address, pincode, latitude, longitude
                FROM customers
                WHERE customer_id = ?
            """, (event["order"]["customer_id"],))
            
            customer_data = cursor.fetchone()
            if not customer_data:
                logger.error(f"Customer {event['order']['customer_id']} not found")
                return False
            
            # Insert order
            cursor.execute("""
                INSERT INTO orders (
                    order_id, customer_id, warehouse_id, order_date,
                    shipping_address, shipping_pincode, delivery_address, delivery_latitude, delivery_longitude,
                    total_amount, status, payment_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event["order"]["order_id"],
                event["order"]["customer_id"],
                event["order"]["warehouse_id"],
                event["order"]["order_date"],
                customer_data[0],  # shipping_address (same as customer address)
                customer_data[1],  # shipping_pincode (same as customer pincode)
                customer_data[0],  # delivery_address (same as customer address)
                customer_data[2],  # latitude
                customer_data[3],  # longitude
                event["order"]["total_amount"],
                event["order"]["status"],
                event["order"]["payment_method"]
            ))
            
            # Insert order items
            for item in event["order_items"]:
                cursor.execute("""
                    INSERT INTO order_items (
                        order_id, product_id, quantity, unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    item["order_id"],
                    item["product_id"],
                    item["quantity"],
                    item["unit_price"],
                    item["total_price"]
                ))
                
                # Update inventory
                cursor.execute("""
                    UPDATE inventory
                    SET current_stock = current_stock - ?
                    WHERE warehouse_id = ? AND product_id = ?
                """, (
                    item["quantity"],
                    event["order"]["warehouse_id"],
                    item["product_id"]
                ))
                
                # Record inventory change
                cursor.execute("""
                    INSERT INTO inventory_changes (
                        warehouse_id, product_id, change_type, quantity_change, reason, reference_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event["order"]["warehouse_id"],
                    item["product_id"],
                    "sale",
                    -item["quantity"],
                    "Order placed",
                    event["order"]["order_id"]
                ))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving event to database: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def run_simulation(self):
        """Run the simulation continuously."""
        global running
        
        logger.info(f"Starting live event simulation at {self.events_per_minute} events per minute")
        
        while running:
            try:
                event = self.generate_event()
                if event:
                    if self.save_event(event):
                        self.event_count += 1
                        logger.info(f"Generated event #{self.event_count}: Order {event['order']['order_id']} with {len(event['order_items'])} items")
                        
                        # Add to queue for processing by other threads
                        event_queue.put(event)
                    else:
                        logger.warning("Failed to save event")
                
                # Sleep for the calculated time
                time.sleep(self.sleep_time)
                
            except Exception as e:
                logger.error(f"Error in simulation: {str(e)}", exc_info=True)
                time.sleep(5)  # Sleep longer on error
        
        logger.info(f"Simulation stopped after generating {self.event_count} events")

def process_events():
    """Process events from the queue (simulating background processing)."""
    global running
    
    logger.info("Starting event processor")
    
    while running:
        try:
            # Get event with timeout to allow checking the running flag
            try:
                event = event_queue.get(timeout=1)
                
                # Simulate processing time
                process_time = random.uniform(0.5, 2.0)
                time.sleep(process_time)
                
                logger.info(f"Processed order {event['order']['order_id']} in {process_time:.2f}s")
                
                # Mark as done
                event_queue.task_done()
                
            except Exception:
                # Timeout or other error, just continue
                pass
                
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}", exc_info=True)
            time.sleep(1)
    
    logger.info("Event processor stopped")

def signal_handler(sig, frame):
    """Handle interrupt signals to gracefully stop the simulation."""
    global running
    logger.info("Stopping simulation (Ctrl+C pressed)...")
    running = False

def main():
    """Main function to run the live event simulation."""
    global running
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Simulate live purchase events')
    parser.add_argument('--db-path', type=str, 
                        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'warehouse.db'),
                        help='Path to the SQLite database')
    parser.add_argument('--events-per-minute', type=int, default=10,
                        help='Number of events to generate per minute')
    parser.add_argument('--duration', type=int, default=0,
                        help='Duration of simulation in seconds (0 for indefinite)')
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db_path):
        logger.error(f"Database file not found at {args.db_path}. Please run setup_database.py first.")
        return 1
    
    # Create simulator
    simulator = LiveEventSimulator(args.db_path, args.events_per_minute)
    
    # Load data
    if not simulator.load_data():
        logger.error("Failed to load data for simulation")
        return 1
    
    # Create and start threads
    simulator_thread = threading.Thread(target=simulator.run_simulation)
    processor_thread = threading.Thread(target=process_events)
    
    simulator_thread.daemon = True
    processor_thread.daemon = True
    
    simulator_thread.start()
    processor_thread.start()
    
    try:
        # Run for specified duration or indefinitely
        if args.duration > 0:
            logger.info(f"Simulation will run for {args.duration} seconds")
            time.sleep(args.duration)
            running = False
        else:
            logger.info("Simulation running indefinitely. Press Ctrl+C to stop.")
            # Keep main thread alive
            while running:
                time.sleep(1)
    except KeyboardInterrupt:
        # This should be caught by the signal handler
        pass
    
    # Wait for threads to finish
    logger.info("Waiting for threads to finish...")
    simulator_thread.join(timeout=5)
    processor_thread.join(timeout=5)
    
    logger.info("Simulation completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
