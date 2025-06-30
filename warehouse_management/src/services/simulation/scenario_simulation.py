"""
Scenario simulation module for the warehouse management system.

This module provides functions for running predefined simulation scenarios.
"""
import logging
import datetime
from typing import Dict, List, Any, Optional

from src.services.simulation import order_simulation, inventory_simulation, delivery_simulation

logger = logging.getLogger(__name__)

# Dictionary of predefined scenarios
SCENARIOS = {
    "normal_operations": {
        "description": "Normal day-to-day operations with standard order volume",
        "config": {
            "daily_order_mean": 100,
            "daily_order_std": 20,
            "weekend_multiplier": 1.5,
            "items_per_order_mean": 3,
            "items_per_order_std": 1,
            "restock_target_fill_percentage": 80,
            "delivery_success_rate": 0.95,
            "avg_delivery_speed_kmh": 20
        }
    },
    "high_demand": {
        "description": "High demand scenario (e.g., festival season)",
        "config": {
            "daily_order_mean": 200,
            "daily_order_std": 30,
            "weekend_multiplier": 1.8,
            "items_per_order_mean": 4,
            "items_per_order_std": 2,
            "restock_target_fill_percentage": 90,
            "delivery_success_rate": 0.92,
            "avg_delivery_speed_kmh": 18
        }
    },
    "supply_chain_disruption": {
        "description": "Supply chain disruption scenario with delayed restocking",
        "config": {
            "daily_order_mean": 100,
            "daily_order_std": 20,
            "weekend_multiplier": 1.5,
            "items_per_order_mean": 3,
            "items_per_order_std": 1,
            "restock_target_fill_percentage": 70,
            "min_restock_delay_days": 3,
            "max_restock_delay_days": 7,
            "delivery_success_rate": 0.95,
            "avg_delivery_speed_kmh": 20
        }
    },
    "bad_weather": {
        "description": "Bad weather scenario affecting deliveries",
        "config": {
            "daily_order_mean": 80,
            "daily_order_std": 30,
            "weekend_multiplier": 1.2,
            "items_per_order_mean": 3,
            "items_per_order_std": 1,
            "restock_target_fill_percentage": 80,
            "delivery_success_rate": 0.85,
            "avg_delivery_speed_kmh": 15,
            "delivery_time_std_minutes": 30
        }
    },
    "new_product_launch": {
        "description": "New product launch scenario with focused demand",
        "config": {
            "daily_order_mean": 150,
            "daily_order_std": 40,
            "weekend_multiplier": 1.5,
            "items_per_order_mean": 2,
            "items_per_order_std": 1,
            "restock_target_fill_percentage": 85,
            "delivery_success_rate": 0.93,
            "avg_delivery_speed_kmh": 20,
            "new_product_focus": True,
            "new_product_percentage": 40
        }
    }
}

def run_scenario(scenario_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a predefined scenario simulation.
    
    Args:
        scenario_name: Name of scenario to run
        config: Additional configuration to override defaults
        
    Returns:
        Dictionary with simulation results
    """
    # Check if scenario exists
    if scenario_name not in SCENARIOS:
        logger.error(f"Unknown scenario: {scenario_name}")
        return {
            "status": "error",
            "message": f"Unknown scenario: {scenario_name}. Available scenarios: {list(SCENARIOS.keys())}"
        }
    
    # Get scenario configuration
    scenario = SCENARIOS[scenario_name]
    scenario_config = scenario["config"].copy()
    
    # Override with provided config
    scenario_config.update(config)
    
    logger.info(f"Running scenario: {scenario_name} - {scenario['description']}")
    
    # Run simulation
    results = run_end_to_end_simulation(
        config=scenario_config,
        duration_days=config.get("duration_days", 7),
        start_date=config.get("start_date")
    )
    
    # Add scenario information
    results["scenario"] = {
        "name": scenario_name,
        "description": scenario["description"]
    }
    
    return results

def run_end_to_end_simulation(config: Dict[str, Any],
                            duration_days: int = 7,
                            start_date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    Run an end-to-end simulation with all components.
    
    Args:
        config: Simulation configuration
        duration_days: Duration of simulation in days
        start_date: Start date for simulation
        
    Returns:
        Dictionary with simulation results
    """
    # Convert start_date string to date object if needed
    if isinstance(start_date, str):
        start_date = datetime.datetime.fromisoformat(start_date).date()
    elif start_date is None:
        start_date = datetime.date.today()
    
    # Simulate orders
    logger.info(f"Simulating orders for {duration_days} days from {start_date}")
    order_results = order_simulation.simulate_orders(
        config=config,
        duration_days=duration_days,
        start_date=start_date
    )
    
    if order_results["status"] != "success":
        return order_results
    
    # Simulate inventory based on orders
    logger.info("Simulating inventory changes")
    inventory_results = inventory_simulation.simulate_inventory(
        config=config,
        order_data=order_results.get("orders", [])
    )
    
    # Simulate deliveries based on orders
    logger.info("Simulating deliveries")
    delivery_results = delivery_simulation.simulate_deliveries(
        config=config,
        order_data=order_results.get("orders", [])
    )
    
    # Combine results
    return {
        "status": "success",
        "duration_days": duration_days,
        "start_date": start_date.isoformat(),
        "end_date": (start_date + datetime.timedelta(days=duration_days)).isoformat(),
        "config": config,
        "order_simulation": order_results,
        "inventory_simulation": inventory_results,
        "delivery_simulation": delivery_results,
        "summary": {
            "total_orders": len(order_results.get("orders", [])),
            "total_revenue": sum(order.get("total_amount", 0) for order in order_results.get("orders", [])),
            "inventory_changes": inventory_results.get("summary", {}),
            "delivery_metrics": delivery_results.get("summary", {})
        }
    }

def get_available_scenarios() -> Dict[str, Dict[str, Any]]:
    """
    Get list of available scenarios with descriptions.
    
    Returns:
        Dictionary of scenario information
    """
    scenario_info = {}
    
    for name, scenario in SCENARIOS.items():
        scenario_info[name] = {
            "description": scenario["description"],
            "key_parameters": {k: v for k, v in scenario["config"].items() 
                             if k in ["daily_order_mean", "delivery_success_rate", "restock_target_fill_percentage"]}
        }
    
    return scenario_info

def create_custom_scenario(name: str, description: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a custom scenario configuration.
    
    Args:
        name: Name for the scenario
        description: Description of the scenario
        config: Configuration parameters
        
    Returns:
        Dictionary with scenario information
    """
    # Validate required configuration
    required_params = [
        "daily_order_mean",
        "daily_order_std",
        "weekend_multiplier",
        "items_per_order_mean",
        "delivery_success_rate"
    ]
    
    missing_params = [param for param in required_params if param not in config]
    
    if missing_params:
        return {
            "status": "error",
            "message": f"Missing required parameters: {missing_params}"
        }
    
    # Create scenario
    scenario = {
        "description": description,
        "config": config
    }
    
    # Add to scenarios dictionary (in memory only)
    SCENARIOS[name] = scenario
    
    return {
        "status": "success",
        "message": f"Created custom scenario: {name}",
        "scenario": {
            "name": name,
            "description": description,
            "config": config
        }
    }
