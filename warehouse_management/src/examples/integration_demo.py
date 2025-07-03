"""
Integration demonstration for the warehouse management system.

This script demonstrates how to integrate simulation and reporting modules
to create a complete end-to-end workflow.
"""
import os
import sys
import logging
import datetime
from pathlib import Path
import json
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


from src.services.simulation.order_simulation import OrderSimulation
from src.services.simulation.inventory_simulation import InventorySimulation
from src.services.simulation.delivery_simulation import DeliverySimulation
from src.services.simulation.scenario_simulation import ScenarioSimulation

from src.services.reporting.report_generator import ReportGenerator
from src.services.reporting.inventory_reports import InventoryReports
from src.services.reporting.order_reports import OrderReports
from src.services.reporting.delivery_reports import DeliveryReports
from src.services.reporting.performance_reports import PerformanceReports

from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """Run the integration demonstration."""
    logger.info("Starting integration demonstration")
    
    # Create output directories
    output_dir = Path("./outputs")
    data_dir = output_dir / "integration_data"
    reports_dir = output_dir / "integration_reports"
    
    for directory in [data_dir, reports_dir]:
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
    
    # Initialize reporting components
    report_generator = ReportGenerator(
        templates_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    )
    inventory_reports = InventoryReports(report_generator)
    order_reports = OrderReports(report_generator)
    delivery_reports = DeliveryReports(report_generator)
    performance_reports = PerformanceReports(report_generator)
    
    # Step 1: Run a simulation scenario
    logger.info("Running simulation scenario: high_demand")
    
    # Set date range for simulation
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    
    # Create a custom high demand scenario
    high_demand_config = {
        "name": "high_demand_holiday",
        "description": "High demand during holiday season",
        "duration_days": 30,
        "start_date": start_date,
        "end_date": end_date,
        "order_config": {
            "order_pattern": "peak_hours",
            "order_volume_multiplier": 2.0,
            "avg_items_per_order": 5
        },
        "inventory_config": {
            "restock_pattern": "predictive",
            "stockout_probability": 0.1
        },
        "delivery_config": {
            "num_agents": 20,
            "max_deliveries_per_agent": 15,
            "delivery_time_multiplier": 1.1
        }
    }
    
    # Run the scenario
    scenario_results = scenario_sim.create_and_run_custom_scenario(high_demand_config)
    
    # Save scenario results
    with open(data_dir / "high_demand_scenario_results.json", 'w') as f:
        json.dump(scenario_results, f, indent=2, default=str)
    
    # Extract data from scenario results
    orders = scenario_results.get("orders", [])
    inventory_changes = scenario_results.get("inventory_changes", [])
    deliveries = scenario_results.get("deliveries", [])
    
    # Ensure consistent attribute names
    for order in orders:
        if 'id' in order and 'order_id' not in order:
            order['order_id'] = order['id']
            
    for inventory in inventory_changes:
        if 'id' in inventory and 'inventory_id' not in inventory:
            inventory['inventory_id'] = inventory['id']
            
    for delivery in deliveries:
        if 'id' in delivery and 'delivery_id' not in delivery:
            delivery['delivery_id'] = delivery['id']
    
    # Save extracted data to CSV for analysis
    pd.DataFrame(orders).to_csv(data_dir / "simulated_orders.csv", index=False)
    pd.DataFrame(inventory_changes).to_csv(data_dir / "simulated_inventory.csv", index=False)
    pd.DataFrame(deliveries).to_csv(data_dir / "simulated_deliveries.csv", index=False)
    
    # Calculate summary statistics if not provided by the scenario
    if "summary" not in scenario_results:
        # Calculate average order value
        total_order_value = sum(order.get("total_amount", 0) for order in orders)
        avg_order_value = total_order_value / len(orders) if orders else 0
        
        # Create summary dictionary
        scenario_results["summary"] = {
            "total_orders": len(orders),
            "total_order_value": total_order_value,
            "avg_order_value": avg_order_value,
            "total_inventory_changes": len(inventory_changes),
            "total_deliveries": len(deliveries),
            "on_time_delivery_rate": 0.95,  # Mock value for demo
            "stockout_rate": 0.05,  # Mock value for demo
            "total_revenue": total_order_value  # Use total order value as revenue
        }
    
    logger.info(f"Simulation completed with {len(orders)} orders, {len(inventory_changes)} inventory changes, and {len(deliveries)} deliveries")
    
    # Step 2: Generate reports based on simulation data
    logger.info("Generating reports based on simulation data")
    
    # Mock database insertion (in a real system, this would insert into the database)
    logger.info("Note: In a production system, simulation data would be inserted into the database")
    logger.info("For this demo, we'll generate reports directly from the simulation data")
    
    # Generate inventory report
    inventory_report_path = inventory_reports.generate_inventory_snapshot(
        output_format='html',
        filename=os.path.join(reports_dir, "inventory_snapshot.html")
    )
    logger.info(f"Inventory snapshot report generated: {inventory_report_path}")
    
    # Generate order report
    order_report_path = order_reports.generate_order_summary(
        start_date=start_date.date(),
        end_date=end_date.date(),
        output_format='html',
        filename=os.path.join(reports_dir, "order_summary.html")
    )
    logger.info(f"Order summary report generated: {order_report_path}")
    
    # Generate sales report
    sales_report_path = order_reports.generate_sales_report(
        start_date=start_date.date(),
        end_date=end_date.date(),
        group_by='day',
        output_format='html',
        filename=os.path.join(reports_dir, "sales_report.html")
    )
    logger.info(f"Sales report generated: {sales_report_path}")
    
    # Generate delivery report
    delivery_report_path = delivery_reports.generate_delivery_performance(
        start_date=start_date.date(),
        end_date=end_date.date(),
        output_format='html',
        filename=os.path.join(reports_dir, "delivery_performance.html")
    )
    logger.info(f"Delivery performance report generated: {delivery_report_path}")
    
    # Generate warehouse efficiency report
    warehouse_report_path = performance_reports.generate_warehouse_efficiency(
        start_date=start_date.date(),
        end_date=end_date.date(),
        output_format='html',
        filename=os.path.join(reports_dir, "warehouse_efficiency.html")
    )
    logger.info(f"Warehouse efficiency report generated: {warehouse_report_path}")
    
    # Step 3: Generate a comprehensive scenario analysis report
    logger.info("Generating comprehensive scenario analysis report")
    
    # Create a custom report with scenario analysis
    scenario_analysis = {
        "title": "High Demand Holiday Scenario Analysis",
        "generated_at": datetime.datetime.now().isoformat(),
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat()
        },
        "scenario": high_demand_config,
        "summary": scenario_results["summary"],
        "key_findings": [
            f"Processed {len(orders)} orders over {high_demand_config['duration_days']} days",
            f"Average order value: ${scenario_results['summary']['avg_order_value']:.2f}",
            f"On-time delivery rate: {scenario_results['summary']['on_time_delivery_rate']*100:.1f}%",
            f"Stockout rate: {scenario_results['summary']['stockout_rate']*100:.1f}%",
            f"Total revenue: ${scenario_results['summary']['total_revenue']:.2f}"
        ],
        "recommendations": [
            "Increase delivery agent capacity during peak hours",
            "Implement predictive inventory management to reduce stockouts",
            "Consider dynamic pricing to balance demand during peak periods",
            "Optimize warehouse operations to handle increased order volume"
        ],
        "generate_charts": True
    }
    
    # Generate the scenario analysis report
    scenario_report_path = report_generator.generate_report(
        data=scenario_analysis,
        report_type="scenario_analysis",
        output_format='html',
        filename=os.path.join(reports_dir, "scenario_analysis.html")
    )
    logger.info(f"Scenario analysis report generated: {scenario_report_path}")
    
    # Step 4: Export all reports in different formats
    logger.info("Exporting reports in different formats")
    
    formats = ['json', 'csv']
    for fmt in formats:
        try:
            path = report_generator.generate_report(
                data=scenario_analysis,
                report_type="scenario_analysis",
                output_format=fmt,
                filename=os.path.join(reports_dir, f"scenario_analysis.{fmt}")
            )
            logger.info(f"Scenario analysis exported in {fmt} format: {path}")
        except Exception as e:
            logger.error(f"Failed to generate {fmt} report: {str(e)}")
    
    logger.info("Integration demonstration completed")
    logger.info(f"Simulation data saved to {data_dir}")
    logger.info(f"Reports saved to {reports_dir}")
    
    # Provide instructions for next steps
    logger.info("\nNext steps:")
    logger.info("1. Review the generated reports in the 'outputs/integration_reports' directory")
    logger.info("2. Analyze the simulation data in the 'outputs/integration_data' directory")
    logger.info("3. Modify the scenario configuration to test different business conditions")

if __name__ == "__main__":
    main()
