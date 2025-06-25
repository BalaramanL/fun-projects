"""
Component-specific demos for the advanced elevator system.

This module contains isolated demos for each major component of the advanced elevator system,
allowing for independent testing and verification of component functionality.

Each demo function focuses on a specific component and demonstrates its key features.
"""

import asyncio
from datetime import datetime, timedelta
import random
import time

import sys
import os

# Add parent directory to path to allow imports from elevator package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from models import Direction, ElevatorState, FloorRequest, DestinationRequest
from systems import (
    AdvancedElevator, OccupancySensor, PeopleDistributionEstimator,
    DynamicElevatorTracker, AdvancedRequestCoordinator,
    BiDirectionalRequest, FloorRequestBatch, ElevatorAssignment
)


async def demo_occupancy_sensor():
    """Demo the OccupancySensor component."""
    print("\n=== OccupancySensor Demo ===")
    
    # Create sensor
    sensor = OccupancySensor()
    
    # Test initial state
    print(f"Initial occupancy: {sensor.current_occupancy}")
    print(f"Initial available capacity: {sensor.get_available_capacity()}")
    
    # Test adding people
    sensor.update_occupancy(5)
    print(f"After adding 5 people: {sensor.current_occupancy}")
    print(f"Available capacity: {sensor.get_available_capacity()}")
    
    # Test adding more people
    sensor.update_occupancy(8)  # Set to 8 total
    print(f"After setting to 8 people: {sensor.current_occupancy}")
    print(f"Available capacity: {sensor.get_available_capacity()}")
    
    # Test removing people
    sensor.update_occupancy(4)  # Set to 4 total
    print(f"After setting to 4 people: {sensor.current_occupancy}")
    print(f"Available capacity: {sensor.get_available_capacity()}")
    
    print("\n==================================================\n")


async def demo_advanced_elevator():
    """Demo the AdvancedElevator component."""
    print("\n=== AdvancedElevator Demo ===")
    
    # Create elevator
    elevator = AdvancedElevator("E1", current_floor=5)
    print(f"Created elevator {elevator.id} at floor {elevator.current_floor}")
    print(f"Initial state: {elevator.state}")
    print(f"Initial direction: {elevator.direction}")
    
    # Add destinations
    print("\nAdding destinations...")
    elevator.add_destination(8)
    print(f"Added destination 8 to elevator {elevator.id}")
    
    elevator.add_destination(3)
    print(f"Added destination 3 to elevator {elevator.id}")
    
    elevator.add_destination(10)
    print(f"Added destination 10 to elevator {elevator.id}")
    
    # Show destinations and direction
    floors = [req.floor for req in elevator.destination_requests]
    print(f"Destination requests: {floors}")
    print(f"Current direction: {elevator.direction}")
    
    # Move elevator
    print("\nMoving elevator...")
    for _ in range(5):  # Move up to 5 floors
        next_floor = elevator.get_next_destination()
        if next_floor:
            print(f"Next destination: {next_floor}")
            await elevator.move_to_next_floor()
            print(f"Moved to floor {elevator.current_floor}")
            
            # If we reached a destination, open doors
            if elevator.current_floor in floors and elevator.current_floor == next_floor:
                print(f"Reached destination floor {elevator.current_floor}")
                await elevator.open_doors()
                print("Doors opened")
                
                # Simulate people entering/exiting
                people_count = 3 if elevator.direction == Direction.DOWN else 5
                print(f"{people_count} people {'exiting' if elevator.direction == Direction.DOWN else 'entering'}")
                elevator.update_occupancy(people_count if elevator.direction == Direction.UP else -people_count)
                
                await elevator.close_doors()
                print("Doors closed")
    
    # Test maintenance mode
    print("\nTesting maintenance mode...")
    elevator.enter_maintenance_mode()
    print(f"Elevator state after entering maintenance: {elevator.state}")
    
    # Try to add destination in maintenance mode
    try:
        elevator.add_destination(7)
        print("Added destination while in maintenance (shouldn't happen)")
    except Exception as e:
        print(f"Correctly rejected destination while in maintenance: {e}")
    
    # Exit maintenance mode
    elevator.exit_maintenance_mode()
    print(f"Elevator state after exiting maintenance: {elevator.state}")
    
    print("\n==================================================\n")


async def demo_people_distribution_estimator():
    """Demo the PeopleDistributionEstimator component."""
    print("\n=== PeopleDistributionEstimator Demo ===")
    
    # Create estimator
    estimator = PeopleDistributionEstimator(total_floors=20)
    
    # Test different floors and times
    test_cases = [
        (5, 10, 9),    # Floor 5, 10 people, 9 AM
        (10, 8, 12),   # Floor 10, 8 people, 12 PM
        (15, 12, 17),  # Floor 15, 12 people, 5 PM
        (2, 6, 8),     # Floor 2, 6 people, 8 AM
        (18, 5, 22)    # Floor 18, 5 people, 10 PM
    ]
    
    for floor, people, hour in test_cases:
        up, down = estimator.estimate_distribution(floor, people, hour)
        print(f"Floor {floor} at {hour}:00 with {people} people: {up} UP, {down} DOWN")
    
    print("\n==================================================\n")


async def demo_dynamic_elevator_tracker():
    """Demo the DynamicElevatorTracker component."""
    print("\n=== DynamicElevatorTracker Demo ===")
    
    # Create tracker
    tracker = DynamicElevatorTracker()
    
    # Create elevators
    elevators = [
        AdvancedElevator("E1", current_floor=5),
        AdvancedElevator("E2", current_floor=10),
        AdvancedElevator("E3", current_floor=15)
    ]
    
    # Add destinations to elevators
    elevators[0].add_destination(8)
    elevators[0].add_destination(12)
    
    elevators[1].add_destination(7)
    elevators[1].add_destination(3)
    
    elevators[2].enter_maintenance_mode()
    
    # Calculate completion times
    print("\nCalculating service completion times:")
    for elevator in elevators:
        completion_time = tracker.calculate_service_completion_time(elevator)
        
        # Format the time nicely
        time_str = completion_time.strftime("%H:%M:%S")
        
        print(f"Elevator {elevator.id} at floor {elevator.current_floor}, " +
              f"state: {elevator.state}, " +
              f"destinations: {[req.floor for req in elevator.destination_requests]}, " +
              f"completion time: {time_str}")
    
    # Find next available elevator
    print("\nFinding next available elevator for different floors:")
    test_floors = [3, 8, 15]
    
    for floor in test_floors:
        elevator, arrival_time = tracker.find_next_available_elevator(elevators, floor)
        
        if elevator:
            # Format the time nicely
            time_str = arrival_time.strftime("%H:%M:%S")
            
            print(f"For floor {floor}, best elevator is {elevator.id}, " +
                  f"estimated arrival: {time_str}")
        else:
            print(f"No elevator available for floor {floor}")
    
    # Update elevator schedules
    print("\nUpdating elevator schedules:")
    
    # Set a future time
    future_time = datetime.now() + timedelta(minutes=5)
    tracker.update_elevator_schedule("E1", future_time, "serving floor 8")
    
    # Check updated schedule
    elevator, arrival_time = tracker.find_next_available_elevator(elevators, 8)
    if elevator:
        print(f"After schedule update, best elevator for floor 8 is {elevator.id}, " +
              f"estimated arrival: {arrival_time.strftime('%H:%M:%S')}")
    
    print("\n==================================================\n")


async def demo_advanced_request_coordinator():
    """Demo the AdvancedRequestCoordinator component."""
    print("\n=== AdvancedRequestCoordinator Demo ===")
    
    # Create coordinator
    coordinator = AdvancedRequestCoordinator()
    
    # Create elevators
    elevators = [
        AdvancedElevator("E1", current_floor=5),
        AdvancedElevator("E2", current_floor=10),
        AdvancedElevator("E3", current_floor=15)
    ]
    
    # Add some requests
    print("\nAdding requests:")
    
    # Regular directional request
    req1_id = coordinator.add_floor_request(floor=3, direction=Direction.UP, people_count=4)
    print(f"Added UP request at floor 3 with 4 people, ID: {req1_id}")
    
    # Bi-directional request
    req2_id = coordinator.add_floor_request(floor=12, direction="BOTH", people_count=8)
    print(f"Added BOTH request at floor 12 with 8 people, ID: {req2_id}")
    
    # Large request
    req3_id = coordinator.add_floor_request(floor=18, direction=Direction.DOWN, people_count=15)
    print(f"Added large DOWN request at floor 18 with 15 people, ID: {req3_id}")
    
    # Process requests
    print("\nProcessing requests:")
    assignments = await coordinator.process_requests_with_reassignment(elevators)
    
    print(f"Created {len(assignments)} assignments:")
    for i, assignment in enumerate(assignments):
        print(f"Assignment {i+1}: Elevator {assignment.elevator_id} to request {assignment.request_id}, " +
              f"Expected capacity: {assignment.expected_capacity}, " +
              f"Arrival time: {assignment.estimated_arrival_time.strftime('%H:%M:%S')}, " +
              f"Completion time: {assignment.estimated_service_completion_time.strftime('%H:%M:%S')}")
    
    # Resolve bi-directional request
    print("\nResolving bi-directional distribution:")
    coordinator.resolve_bidirectional_distribution(
        request_id=req2_id,
        actual_up=3,
        actual_down=5
    )
    
    # Process again after resolution
    print("\nProcessing after bi-directional resolution:")
    assignments = await coordinator.process_requests_with_reassignment(elevators)
    
    print(f"Created {len(assignments)} assignments:")
    for i, assignment in enumerate(assignments):
        print(f"Assignment {i+1}: Elevator {assignment.elevator_id} to request {assignment.request_id}, " +
              f"Expected capacity: {assignment.expected_capacity}, " +
              f"Arrival time: {assignment.estimated_arrival_time.strftime('%H:%M:%S')}, " +
              f"Completion time: {assignment.estimated_service_completion_time.strftime('%H:%M:%S')}")
    
    # Test dynamic reassignment
    print("\nTesting dynamic reassignment:")
    
    # Create a long-waiting request
    long_wait_batch = FloorRequestBatch(
        floor=15,
        direction=Direction.UP,
        total_people_waiting=3
    )
    long_wait_batch.creation_time = datetime.now() - timedelta(minutes=5)  # 5 minutes ago
    coordinator.active_batches[long_wait_batch.request_id] = long_wait_batch
    
    print(f"Added request at floor 15 with 3 people that has been waiting " +
          f"for {long_wait_batch.wait_time_minutes:.1f} minutes")
    
    # Process with reassignment opportunity
    assignments = await coordinator.process_requests_with_reassignment(elevators)
    
    print(f"Created {len(assignments)} assignments:")
    for i, assignment in enumerate(assignments):
        print(f"Assignment {i+1}: Elevator {assignment.elevator_id} to request {assignment.request_id}, " +
              f"Expected capacity: {assignment.expected_capacity}, " +
              f"Arrival time: {assignment.estimated_arrival_time.strftime('%H:%M:%S')}, " +
              f"Completion time: {assignment.estimated_service_completion_time.strftime('%H:%M:%S')}")
    
    # Show system metrics
    print("\nSystem metrics:")
    metrics = coordinator.get_system_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    print("\n==================================================\n")


async def run_all_demos():
    """Run all component demos sequentially."""
    await demo_occupancy_sensor()
    await demo_advanced_elevator()
    await demo_people_distribution_estimator()
    await demo_dynamic_elevator_tracker()
    await demo_advanced_request_coordinator()


if __name__ == "__main__":
    print("Running component-specific demos for the advanced elevator system")
    asyncio.run(run_all_demos())
