"""
Simulation service for the warehouse management system.

This service provides simulation capabilities for:
- Order generation and fulfillment
- Inventory management
- Delivery operations
- System performance analysis

It acts as a facade for specialized simulation modules.
"""
import logging
import datetime
from typing import Dict, List, Any, Optional, Union
import json

from src.utils.helpers import get_db_session
from src.services.simulation import (
    order_simulation,
    inventory_simulation,
    delivery_simulation,
    scenario_simulation
)

logger = logging.getLogger(__name__)

class SimulationService:
    """Service for simulating warehouse operations."""
    
    def __init__(self):
        """Initialize the simulation service."""
        logger.info("SimulationService initialized")
    
    def simulate_orders(self, 
                      config: Dict[str, Any], 
                      duration_days: int = 7,
                      start_date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """
        Simulate order generation and fulfillment.
        
        Args:
            config: Simulation configuration
            duration_days: Duration of simulation in days
            start_date: Start date for simulation (defaults to today)
            
        Returns:
            Dictionary with simulation results
        """
        logger.info(f"Simulating orders for {duration_days} days")
        
        return order_simulation.simulate_orders(
            config=config,
            duration_days=duration_days,
            start_date=start_date
        )
    
    def simulate_inventory(self, 
                         config: Dict[str, Any],
                         order_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Simulate inventory changes based on orders and restocking.
        
        Args:
            config: Simulation configuration
            order_data: Optional order data from simulate_orders
            
        Returns:
            Dictionary with simulation results
        """
        logger.info("Simulating inventory changes")
        
        return inventory_simulation.simulate_inventory(
            config=config,
            order_data=order_data
        )
    
    def simulate_deliveries(self, 
                          config: Dict[str, Any],
                          order_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Simulate delivery operations.
        
        Args:
            config: Simulation configuration
            order_data: Optional order data from simulate_orders
            
        Returns:
            Dictionary with simulation results
        """
        logger.info("Simulating delivery operations")
        
        return delivery_simulation.simulate_deliveries(
            config=config,
            order_data=order_data
        )
    
    def simulate_scenario(self, 
                        scenario_name: str,
                        config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a predefined scenario simulation.
        
        Args:
            scenario_name: Name of scenario to run
            config: Simulation configuration
            
        Returns:
            Dictionary with simulation results
        """
        logger.info(f"Running scenario simulation: {scenario_name}")
        
        return scenario_simulation.run_scenario(
            scenario_name=scenario_name,
            config=config
        )
    
    def simulate_full_operations(self, 
                               config: Dict[str, Any],
                               duration_days: int = 7,
                               start_date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """
        Run a full end-to-end simulation of warehouse operations.
        
        Args:
            config: Simulation configuration
            duration_days: Duration of simulation in days
            start_date: Start date for simulation
            
        Returns:
            Dictionary with simulation results
        """
        logger.info(f"Running full operations simulation for {duration_days} days")
        
        # Simulate orders
        order_results = self.simulate_orders(
            config=config,
            duration_days=duration_days,
            start_date=start_date
        )
        
        # Simulate inventory based on orders
        inventory_results = self.simulate_inventory(
            config=config,
            order_data=order_results.get('orders', [])
        )
        
        # Simulate deliveries based on orders
        delivery_results = self.simulate_deliveries(
            config=config,
            order_data=order_results.get('orders', [])
        )
        
        # Combine results
        return {
            "status": "success",
            "duration_days": duration_days,
            "start_date": start_date.isoformat() if start_date else datetime.date.today().isoformat(),
            "end_date": (start_date + datetime.timedelta(days=duration_days)).isoformat() if start_date else 
                       (datetime.date.today() + datetime.timedelta(days=duration_days)).isoformat(),
            "order_simulation": order_results,
            "inventory_simulation": inventory_results,
            "delivery_simulation": delivery_results,
            "summary": {
                "total_orders": len(order_results.get('orders', [])),
                "total_revenue": sum(order.get('total_amount', 0) for order in order_results.get('orders', [])),
                "inventory_changes": inventory_results.get('summary', {}),
                "delivery_metrics": delivery_results.get('summary', {})
            }
        }
    
    def save_simulation_results(self, results: Dict[str, Any], name: str) -> str:
        """
        Save simulation results to file.
        
        Args:
            results: Simulation results
            name: Name for saved results
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_{name}_{timestamp}.json"
        filepath = f"data/simulations/{filename}"
        
        # Ensure directory exists
        import os
        os.makedirs("data/simulations", exist_ok=True)
        
        # Save results
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Saved simulation results to {filepath}")
        return filepath
    
    def load_simulation_results(self, filepath: str) -> Dict[str, Any]:
        """
        Load simulation results from file.
        
        Args:
            filepath: Path to results file
            
        Returns:
            Dictionary with simulation results
        """
        try:
            with open(filepath, 'r') as f:
                results = json.load(f)
            
            logger.info(f"Loaded simulation results from {filepath}")
            return results
        except Exception as e:
            logger.error(f"Error loading simulation results: {str(e)}")
            return {"status": "error", "message": f"Error loading results: {str(e)}"}
    
    def compare_simulations(self, 
                          simulation1: Dict[str, Any], 
                          simulation2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two simulation results.
        
        Args:
            simulation1: First simulation results
            simulation2: Second simulation results
            
        Returns:
            Dictionary with comparison results
        """
        logger.info("Comparing simulation results")
        
        # Extract key metrics
        metrics1 = self._extract_metrics(simulation1)
        metrics2 = self._extract_metrics(simulation2)
        
        # Calculate differences
        differences = {}
        for key in set(metrics1.keys()) | set(metrics2.keys()):
            if key in metrics1 and key in metrics2:
                val1 = metrics1[key]
                val2 = metrics2[key]
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    abs_diff = val2 - val1
                    pct_diff = (val2 - val1) / val1 * 100 if val1 != 0 else float('inf')
                    
                    differences[key] = {
                        "value1": val1,
                        "value2": val2,
                        "absolute_diff": abs_diff,
                        "percentage_diff": pct_diff
                    }
        
        return {
            "status": "success",
            "simulation1": {
                "name": simulation1.get("name", "Simulation 1"),
                "metrics": metrics1
            },
            "simulation2": {
                "name": simulation2.get("name", "Simulation 2"),
                "metrics": metrics2
            },
            "differences": differences
        }
    
    def _extract_metrics(self, simulation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key metrics from simulation results.
        
        Args:
            simulation: Simulation results
            
        Returns:
            Dictionary with key metrics
        """
        metrics = {}
        
        # Extract order metrics
        if "order_simulation" in simulation:
            order_sim = simulation["order_simulation"]
            metrics["total_orders"] = len(order_sim.get("orders", []))
            metrics["total_revenue"] = sum(order.get("total_amount", 0) for order in order_sim.get("orders", []))
            
            # Count by status
            status_counts = {}
            for order in order_sim.get("orders", []):
                status = order.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                metrics[f"orders_{status}"] = count
        
        # Extract inventory metrics
        if "inventory_simulation" in simulation:
            inv_sim = simulation["inventory_simulation"]
            summary = inv_sim.get("summary", {})
            
            for key, value in summary.items():
                metrics[f"inventory_{key}"] = value
        
        # Extract delivery metrics
        if "delivery_simulation" in simulation:
            del_sim = simulation["delivery_simulation"]
            summary = del_sim.get("summary", {})
            
            for key, value in summary.items():
                metrics[f"delivery_{key}"] = value
        
        return metrics
