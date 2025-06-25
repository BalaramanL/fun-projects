"""
Advanced Elevator System Demo Tests

This module contains demo tests for the advanced elevator system to verify functionality.
"""
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to allow imports from elevator package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from models import Direction, ElevatorState
from systems import (
    AdvancedRequestCoordinator, AdvancedElevator,
    BiDirectionalRequest, FloorRequestBatch,
    CAPACITY_PER_ELEVATOR
)

async def demo_advanced_elevator_system():
    """
    Demonstrate the advanced elevator system with various scenarios.
    
    This demo showcases:
    1. Large request splitting
    2. Bi-directional request handling
    3. Maintenance resilience
    4. Dynamic reassignment
    
    Time Complexity: O(e*r) where e is number of elevators and r is number of requests
    Space Complexity: O(e + r) for tracking elevator and request states
    """
    print("=== Advanced Elevator System Demo ===")
    
    # Create coordinator
    coordinator = AdvancedRequestCoordinator()
    
    # Create elevators
    elevators = [
        AdvancedElevator(f"E{i+1}", current_floor=i*5+1)
        for i in range(3)
    ]
    
    print(f"Created {len(elevators)} elevators at floors: "
          f"{', '.join([str(e.current_floor) for e in elevators])}\n")
    
    # Scenario 1: Large request splitting
    print("\n--- Scenario 1: Large Request Splitting ---")
    large_request_id = coordinator.add_floor_request(
        floor=5, 
        direction=Direction.UP, 
        people_count=CAPACITY_PER_ELEVATOR * 2 + 3  # More than 2 elevators can handle
    )
    print(f"Added large request at floor 5 with {CAPACITY_PER_ELEVATOR * 2 + 3} people")
    
    # Process the large request
    assignments = await coordinator.process_requests_with_reassignment(elevators)
    print(f"Created {len(assignments)} assignments for large request")
    
    for i, assignment in enumerate(assignments):
        elevator = next(e for e in elevators if e.id == assignment.elevator_id)
        print(f"Assignment {i+1}: Elevator {elevator.id} from floor {elevator.current_floor} "
              f"to floor 5, capacity: {assignment.expected_capacity}")
    
    # Scenario 2: Bi-directional request
    print("\n--- Scenario 2: Bi-directional Request Handling ---")
    bi_request_id = coordinator.add_floor_request(
        floor=10,
        direction="BOTH",
        people_count=15
    )
    print(f"Added bi-directional request at floor 10 with 15 people")
    
    # Get the bi-directional request
    bi_req = coordinator.bidirectional_requests[bi_request_id]
    print(f"Estimated distribution: {bi_req.estimated_up_people} UP, "
          f"{bi_req.estimated_down_people} DOWN")
    
    # Process the bi-directional request
    await coordinator.process_requests_with_reassignment(elevators)
    
    # Simulate elevator arrival and distribution resolution
    coordinator.resolve_bidirectional_distribution(
        request_id=bi_request_id,
        actual_up=8,
        actual_down=7
    )
    
    # Process again after resolution
    await coordinator.process_requests_with_reassignment(elevators)
    
    # Scenario 3: Maintenance resilience
    print("\n--- Scenario 3: Maintenance Resilience ---")
    # Put one elevator in maintenance mode
    elevators[0].enter_maintenance_mode()
    print(f"Elevator {elevators[0].id} entered maintenance mode")
    
    # Add a new request
    maintenance_request_id = coordinator.add_floor_request(
        floor=7,
        direction=Direction.DOWN,
        people_count=5
    )
    print(f"Added request at floor 7 with 5 people going DOWN")
    
    # Process with one elevator in maintenance
    assignments = await coordinator.process_requests_with_reassignment(elevators)
    
    if assignments:
        print(f"Request assigned to elevator {assignments[0].elevator_id} "
              f"despite one elevator in maintenance")
    else:
        print("No elevators available for assignment")
    
    # Scenario 4: Dynamic reassignment
    print("\n--- Scenario 4: Dynamic Reassignment ---")
    # Simulate a long-waiting request
    long_wait_batch = FloorRequestBatch(
        floor=12,
        direction=Direction.DOWN,
        total_people_waiting=3
    )
    
    # Artificially age the request
    long_wait_batch.timestamp = datetime.now() - timedelta(minutes=2)
    coordinator.active_batches[long_wait_batch.request_id] = long_wait_batch
    
    print(f"Added request at floor 12 with 3 people that has been waiting "
          f"for {long_wait_batch.wait_time_minutes:.1f} minutes")
    
    # Exit maintenance mode for all elevators
    for elevator in elevators:
        if elevator.state == ElevatorState.MAINTENANCE:
            elevator.exit_maintenance_mode()
    
    # Process with reassignment opportunity
    await coordinator.process_requests_with_reassignment(elevators)
    
    # Show system metrics
    print("\n--- System Metrics ---")
    metrics = coordinator.get_system_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_advanced_elevator_system())
