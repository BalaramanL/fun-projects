"""
Simulation system demonstration for the warehouse management system.

This script demonstrates how to use the simulation modules to run
various scenarios and analyze the results.
"""
import logging
import datetime
import os
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

from src.services.simulation.order_simulation import OrderSimulation
from src.services.simulation.inventory_simulation import InventorySimulation
from src.services.simulation.delivery_simulation import DeliverySimulation
from src.services.simulation.scenario_simulation import ScenarioSimulation
from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """Run the simulation system demonstration."""
    logger.info("Starting simulation system demonstration")
    
    # Create output directories
    output_dir = Path("./outputs")
    data_dir = output_dir / "simulation_data"
    plots_dir = output_dir / "plots"
    
    for directory in [data_dir, plots_dir]:
        directory.mkdir(exist_ok=True, parents=True)
    
    # Define simulation configuration
    config = {
        "daily_order_mean": 100,
        "daily_order_std": 20,
        "weekend_multiplier": 1.5,
        "items_per_order_mean": 3,
        "items_per_order_std": 1,
        "restock_target_fill_percentage": 80,
        "delivery_success_rate": 0.95,
        "avg_delivery_speed_kmh": 20
    }
    
    # Demo 1: Basic Order Simulation
    logger.info("Running basic order simulation")
    start_date = datetime.date.today() - datetime.timedelta(days=30)
    end_date = datetime.date.today()
    duration_days = (end_date - start_date).days
    
    # Create order simulation instance
    order_sim = OrderSimulation(config=config)
    
    # Run order simulation
    order_results = order_sim.simulate(
        duration_days=duration_days,
        start_date=start_date
    )
    orders = order_results.get("orders", [])
    
    # Save order data
    order_df = pd.DataFrame(orders)
    order_df.to_csv(data_dir / "simulated_orders.csv", index=False)
    logger.info(f"Generated {len(orders)} orders")
    
    # Visualize order distribution
    plt.figure(figsize=(10, 6))
    order_df['timestamp'] = pd.to_datetime(order_df['timestamp'])
    order_df.set_index('timestamp')['total_amount'].resample('D').sum().plot(
        title='Daily Order Amount', grid=True
    )
    plt.savefig(plots_dir / "daily_order_amount.png")
    logger.info("Order visualization saved")
    
    # Demo 2: Inventory Simulation
    logger.info("Running inventory simulation")
    
    # Create inventory simulation instance
    inventory_sim = InventorySimulation(config=config)
    
    # Run inventory simulation
    inventory_results = inventory_sim.simulate(
        order_data=orders
    )
    inventory_changes = inventory_results.get("inventory_changes", [])
    
    # Save inventory data
    inventory_df = pd.DataFrame(inventory_changes)
    inventory_df.to_csv(data_dir / "simulated_inventory.csv", index=False)
    logger.info(f"Generated {len(inventory_changes)} inventory changes")
    
    # Demo 3: Delivery Simulation
    logger.info("Running delivery simulation")
    
    # Create delivery simulation instance
    delivery_sim = DeliverySimulation(config=config)
    
    # Run delivery simulation
    delivery_results = delivery_sim.simulate(
        order_data=orders
    )
    deliveries = delivery_results.get("deliveries", [])
    
    # Save delivery data
    delivery_df = pd.DataFrame(deliveries)
    delivery_df.to_csv(data_dir / "simulated_deliveries.csv", index=False)
    logger.info(f"Generated {len(deliveries)} deliveries")
    
    # Visualize delivery performance
    plt.figure(figsize=(10, 6))
    
    # Check if the required columns exist in the DataFrame
    if 'delivery_time_minutes' in delivery_df.columns and 'status' in delivery_df.columns:
        delivery_df['delivery_time_minutes'] = pd.to_numeric(
            delivery_df['delivery_time_minutes'], errors='coerce'
        )
        delivery_df.boxplot(column=['delivery_time_minutes'], by='status')
        plt.title('Delivery Time by Status')
        plt.suptitle('')  # Remove default title
    else:
        # Create a simple placeholder plot if data is missing
        plt.text(0.5, 0.5, 'Delivery time data not available', 
                horizontalalignment='center', verticalalignment='center')
        plt.title('Delivery Time Data Missing')
    
    plt.savefig(plots_dir / "delivery_time_by_status.png")
    logger.info("Delivery visualization saved")
    
    # Demo 4: Scenario Simulation
    logger.info("Running predefined scenarios")
    
    # Create scenario simulation instance
    scenario_sim = ScenarioSimulation(
        order_simulation=order_sim,
        inventory_simulation=inventory_sim,
        delivery_simulation=delivery_sim
    )
    
    # Normal day scenario
    normal_results = scenario_sim.run_scenario("normal_operations", {})
    with open(data_dir / "normal_day_scenario.json", 'w') as f:
        json.dump(normal_results, f, indent=2, default=str)
    logger.info("Normal day scenario completed")
    
    # High demand scenario
    high_demand_results = scenario_sim.run_scenario("high_demand", {})
    with open(data_dir / "high_demand_scenario.json", 'w') as f:
        json.dump(high_demand_results, f, indent=2, default=str)
    logger.info("High demand scenario completed")
    
    # Supply chain disruption scenario
    supply_chain_results = scenario_sim.run_scenario("supply_chain_disruption", {})
    with open(data_dir / "supply_chain_scenario.json", 'w') as f:
        json.dump(supply_chain_results, f, indent=2, default=str)
    logger.info("Supply chain disruption scenario completed")
    
    # Demo 5: Custom Scenario
    logger.info("Running custom scenario")
    custom_scenario_config = {
        "name": "weekend_flash_sale",
        "description": "Weekend flash sale with limited delivery capacity",
        "daily_order_mean": 200,
        "daily_order_std": 40,
        "weekend_multiplier": 2.5,
        "items_per_order_mean": 4,
        "items_per_order_std": 2,
        "restock_target_fill_percentage": 90,
        "delivery_success_rate": 0.9,
        "avg_delivery_speed_kmh": 18,
        "duration_days": 3
    }
    
    # Create and run custom scenario
    custom_results = scenario_sim.create_and_run_custom_scenario(custom_scenario_config)
    with open(data_dir / "custom_scenario.json", 'w') as f:
        json.dump(custom_results, f, indent=2, default=str)
    logger.info("Custom scenario completed")
    
    # Compare scenarios
    logger.info("Comparing scenarios")
    scenarios = {
        "Normal Day": normal_results,
        "High Demand": high_demand_results,
        "Supply Chain Disruption": supply_chain_results,
        "Weekend Flash Sale": custom_results
    }
    
    # Extract key metrics for comparison
    metrics = {}
    for name, results in scenarios.items():
        if "summary" in results:
            metrics[name] = {
                "total_orders": results["summary"].get("total_orders", 0),
                "total_revenue": results["summary"].get("total_revenue", 0)
            }
            
            # Add delivery metrics if available
            if "delivery_metrics" in results["summary"]:
                delivery_metrics = results["summary"]["delivery_metrics"]
                metrics[name]["on_time_rate"] = delivery_metrics.get("on_time_rate", 0)
                metrics[name]["avg_delay_minutes"] = delivery_metrics.get("average_delay_minutes", 0)
    
    # Create comparison dataframe
    comparison_df = pd.DataFrame(metrics).T
    comparison_df.to_csv(data_dir / "scenario_comparison.csv")
    
    # Visualize comparison
    plt.figure(figsize=(12, 8))
    comparison_df.plot(kind='bar', subplots=True, layout=(3, 2), figsize=(12, 10), 
                      grid=True, sharex=False)
    plt.tight_layout()
    plt.savefig(plots_dir / "scenario_comparison.png")
    logger.info("Scenario comparison visualization saved")
    
    logger.info("Simulation system demonstration completed")
    logger.info(f"Output data saved to {data_dir}")
    logger.info(f"Visualizations saved to {plots_dir}")

if __name__ == "__main__":
    main()
