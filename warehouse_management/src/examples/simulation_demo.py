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
    
    # Initialize simulation components
    order_sim = OrderSimulation()
    inventory_sim = InventorySimulation()
    delivery_sim = DeliverySimulation()
    scenario_sim = ScenarioSimulation(
        order_simulation=order_sim,
        inventory_simulation=inventory_sim,
        delivery_simulation=delivery_sim
    )
    
    # Demo 1: Basic Order Simulation
    logger.info("Running basic order simulation")
    orders = order_sim.generate_orders(
        num_orders=100,
        start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        end_date=datetime.datetime.now(),
        order_pattern="random"
    )
    
    # Save order data
    order_df = pd.DataFrame(orders)
    order_df.to_csv(data_dir / "simulated_orders.csv", index=False)
    logger.info(f"Generated {len(orders)} orders")
    
    # Visualize order distribution
    plt.figure(figsize=(10, 6))
    order_df['order_date'] = pd.to_datetime(order_df['order_date'])
    order_df.set_index('order_date')['total_amount'].resample('D').sum().plot(
        title='Daily Order Amount', grid=True
    )
    plt.savefig(plots_dir / "daily_order_amount.png")
    logger.info("Order visualization saved")
    
    # Demo 2: Inventory Simulation
    logger.info("Running inventory simulation")
    inventory_changes = inventory_sim.simulate_inventory_changes(
        orders=orders,
        days=30,
        restock_pattern="threshold_based",
        random_adjustment_probability=0.1
    )
    
    # Save inventory data
    inventory_df = pd.DataFrame(inventory_changes)
    inventory_df.to_csv(data_dir / "simulated_inventory.csv", index=False)
    logger.info(f"Generated {len(inventory_changes)} inventory changes")
    
    # Demo 3: Delivery Simulation
    logger.info("Running delivery simulation")
    deliveries = delivery_sim.simulate_deliveries(
        orders=orders,
        num_agents=10,
        failure_rate=0.05
    )
    
    # Save delivery data
    delivery_df = pd.DataFrame(deliveries)
    delivery_df.to_csv(data_dir / "simulated_deliveries.csv", index=False)
    logger.info(f"Generated {len(deliveries)} deliveries")
    
    # Visualize delivery performance
    plt.figure(figsize=(10, 6))
    delivery_df['delivery_time_minutes'] = pd.to_numeric(
        delivery_df['delivery_time_minutes'], errors='coerce'
    )
    delivery_df.boxplot(column=['delivery_time_minutes'], by='status')
    plt.title('Delivery Time by Status')
    plt.suptitle('')  # Remove default title
    plt.savefig(plots_dir / "delivery_time_by_status.png")
    logger.info("Delivery visualization saved")
    
    # Demo 4: Scenario Simulation
    logger.info("Running predefined scenarios")
    
    # Normal day scenario
    normal_results = scenario_sim.run_scenario("normal_day")
    with open(data_dir / "normal_day_scenario.json", 'w') as f:
        json.dump(normal_results, f, indent=2, default=str)
    logger.info("Normal day scenario completed")
    
    # High demand scenario
    high_demand_results = scenario_sim.run_scenario("high_demand")
    with open(data_dir / "high_demand_scenario.json", 'w') as f:
        json.dump(high_demand_results, f, indent=2, default=str)
    logger.info("High demand scenario completed")
    
    # Supply chain disruption scenario
    supply_chain_results = scenario_sim.run_scenario("supply_chain_disruption")
    with open(data_dir / "supply_chain_scenario.json", 'w') as f:
        json.dump(supply_chain_results, f, indent=2, default=str)
    logger.info("Supply chain disruption scenario completed")
    
    # Demo 5: Custom Scenario
    logger.info("Running custom scenario")
    custom_scenario_config = {
        "name": "weekend_flash_sale",
        "description": "Weekend flash sale with limited delivery capacity",
        "duration_days": 3,
        "order_config": {
            "order_pattern": "peak_hours",
            "order_volume_multiplier": 2.5,
            "avg_items_per_order": 4
        },
        "inventory_config": {
            "restock_pattern": "just_in_time",
            "stockout_probability": 0.15
        },
        "delivery_config": {
            "num_agents": 15,
            "max_deliveries_per_agent": 12,
            "delivery_time_multiplier": 1.2
        }
    }
    
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
        metrics[name] = {
            "total_orders": results["summary"]["total_orders"],
            "total_revenue": results["summary"]["total_revenue"],
            "avg_delivery_time": results["summary"]["avg_delivery_time"],
            "stockout_rate": results["summary"]["stockout_rate"],
            "on_time_delivery_rate": results["summary"]["on_time_delivery_rate"]
        }
    
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
