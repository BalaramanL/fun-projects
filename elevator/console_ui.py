"""
Advanced Console-based UI for the Elevator Emulator.

This module provides a text-based interface for interacting with the advanced elevator system.
"""
import asyncio
import random
import threading
import time
from typing import List, Dict, Any

from models import Direction, ElevatorState
from systems import (
    AdvancedRequestCoordinator, AdvancedElevator, 
    BiDirectionalRequest, FloorRequestBatch,
    MIN_FLOOR, MAX_FLOOR
)
from constants import DEFAULT_TOTAL_FLOORS


class AdvancedConsoleUI:
    """
    Console-based user interface for the advanced elevator system.
    
    Attributes:
        coordinator: The advanced request coordinator
        elevators: List of advanced elevators
        running: Flag indicating if the system is running
        total_floors: Total number of floors in the building
    """
    def __init__(self, coordinator: AdvancedRequestCoordinator = None, 
                 elevators: List[AdvancedElevator] = None,
                 total_floors: int = DEFAULT_TOTAL_FLOORS):
        self.coordinator = coordinator or AdvancedRequestCoordinator()
        self.elevators = elevators or []
        self.running = False
        self.display_thread = None
        self.controller_thread = None
        self.total_floors = total_floors
    
    def display_menu(self):
        """Display the main menu."""
        print("\n===== Advanced Elevator System Console =====")
        print("1. Add Elevator")
        print("2. Add Floor Request")
        print("3. Display System Status")
        print("4. Start System")
        print("5. Stop System")
        print("6. Toggle Maintenance Mode")
        print("7. Display System Metrics")
        print("8. Exit")
        print("==========================================")
    
    def add_elevator(self):
        """Add a new elevator to the system."""
        try:
            floor = int(input(f"Enter starting floor ({MIN_FLOOR}-{MAX_FLOOR}): "))
            if not (MIN_FLOOR <= floor <= MAX_FLOOR):
                print(f"Error: Floor must be between {MIN_FLOOR} and {MAX_FLOOR}")
                return
                
            elevator_id = f"E{len(self.elevators) + 1}"
            elevator = AdvancedElevator(elevator_id, current_floor=floor)
            self.elevators.append(elevator)
            print(f"Added elevator {elevator_id} at floor {floor}")
        except ValueError:
            print("Error: Please enter a valid floor number")
    
    def add_floor_request(self):
        """Add a new floor request."""
        try:
            floor = int(input(f"Enter floor number ({MIN_FLOOR}-{MAX_FLOOR}): "))
            direction_input = input("Enter direction (UP/DOWN/BOTH): ").upper()
            people_count = int(input("Enter number of people: "))
            
            if not (MIN_FLOOR <= floor <= MAX_FLOOR):
                print(f"Error: Floor must be between {MIN_FLOOR} and {MAX_FLOOR}")
                return
            
            if direction_input not in ["UP", "DOWN", "BOTH"]:
                print("Error: Direction must be UP, DOWN, or BOTH")
                return
                
            direction = Direction.UP if direction_input == "UP" else (
                Direction.DOWN if direction_input == "DOWN" else "BOTH"
            )
            
            if people_count <= 0:
                print("Error: People count must be positive")
                return
            
            # Check if floor can have this direction
            if direction == Direction.UP and floor == MAX_FLOOR:
                print(f"Error: Floor {floor} (top floor) can't have UP button")
                return
            if direction == Direction.DOWN and floor == MIN_FLOOR:
                print(f"Error: Floor {floor} (bottom floor) can't have DOWN button")
                return
            
            request_id = self.coordinator.add_floor_request(floor, direction, people_count)
            print(f"Added request {request_id}")
            
        except ValueError:
            print("Error: Please enter valid numbers")
    
    def display_status(self):
        """
        Display the current system status.
        
        Shows all elevators with their current state, floor, occupancy, and assigned requests.
        Also displays any pending requests that haven't been assigned to elevators yet.
        """
        print("\n===== SYSTEM STATUS =====")
        
        print("\nELEVATORS:")
        if not self.elevators:
            print("No elevators registered")
        else:
            for elevator in self.elevators:
                print(f"  {elevator.id}: Floor {elevator.current_floor}, " +
                      f"State: {elevator.state.value}, " +
                      f"Occupancy: {elevator.occupancy_sensor.current_occupancy}/{elevator.occupancy_sensor.get_available_capacity() + elevator.occupancy_sensor.current_occupancy}, " +
                      f"Direction: {elevator.direction.value if elevator.direction else 'NONE'}")
                
                # Show destinations
                if elevator.destination_requests:
                    destinations = ", ".join([str(req.floor) for req in elevator.destination_requests])
                    print(f"    → Destinations: {destinations}")
        
        # Show active batches
        print("\nACTIVE REQUEST BATCHES:")
        if self.coordinator.active_batches:
            for batch in self.coordinator.active_batches.values():
                if not batch.is_fully_served:
                    # Calculate wait time in seconds
                    wait_time_seconds = batch.wait_time_minutes * 60
                    print(f"  Floor {batch.floor} {batch.direction.name} - "
                          f"{batch.people_remaining} people, "
                          f"Waiting: {wait_time_seconds:.1f} seconds")
        else:
            print("No active request batches")
        print("\nBI-DIRECTIONAL REQUESTS:")
        if not self.coordinator.bidirectional_requests:
            print("No bi-directional requests")
        else:
            for req_id, req in self.coordinator.bidirectional_requests.items():
                print(f"  Floor {req.floor} BOTH - " +
                      f"{req.total_people_waiting} people, " +
                      f"Estimated: {req.estimated_up_people} UP, {req.estimated_down_people} DOWN")
        
        print("=======================")
    
    def display_metrics(self):
        """Display system metrics."""
        print("\n===== SYSTEM METRICS =====")
        
        # Coordinator metrics
        metrics = self.coordinator.get_system_metrics()
        print("\nCOORDINATOR METRICS:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        # Elevator metrics
        print("\nELEVATOR METRICS:")
        for elevator in self.elevators:
            print(f"  {elevator.id}:")
            print(f"    Total trips: {elevator.total_trips}")
            print(f"    Total floors traveled: {elevator.total_floors_traveled}")
            print(f"    Total people served: {elevator.total_people_served}")
            print(f"    Idle time (seconds): {elevator.idle_time_seconds:.1f}")
        
        print("=======================")
    
    def toggle_maintenance(self):
        """Toggle maintenance mode for an elevator."""
        if not self.elevators:
            print("No elevators available")
            return
            
        print("Available elevators:")
        for i, elevator in enumerate(self.elevators):
            print(f"{i+1}. {elevator.id} (Floor {elevator.current_floor}, " +
                  f"State: {elevator.state.value})")
        
        try:
            choice = int(input("Select elevator number: "))
            if not (1 <= choice <= len(self.elevators)):
                print("Invalid elevator number")
                return
                
            elevator = self.elevators[choice-1]
            if elevator.state == "MAINTENANCE":
                elevator.exit_maintenance_mode()
                print(f"Elevator {elevator.id} exited maintenance mode")
            else:
                elevator.enter_maintenance_mode()
                print(f"Elevator {elevator.id} entered maintenance mode")
                
        except ValueError:
            print("Error: Please enter a valid number")
    
    async def run_system(self):
        """
        Run the elevator system asynchronously.
        
        This method is the core of the elevator system's operation. It continuously:
        1. Processes floor requests and assigns elevators optimally
        2. Moves elevators to pickup passengers at source floors
        3. Simulates passengers boarding with destinations based on their direction
        4. Moves elevators to passenger destinations
        5. Handles door operations at each stop
        
        The system uses a multi-objective optimization approach to assign elevators
        to floor requests, considering factors like wait time, elevator capacity,
        and current direction of travel.
        
        Time Complexity: O(e*r) where e is number of elevators and r is number of requests
        Space Complexity: O(e + r) for tracking elevator and request states
        """
        while self.running:
            # Process bidirectional requests that haven't been resolved yet
            for req_id, req in list(self.coordinator.bidirectional_requests.items()):
                if not req.is_distribution_known:
                    # Auto-resolve bidirectional requests with the estimated distribution
                    self.coordinator.resolve_bidirectional_distribution(
                        request_id=req_id,
                        actual_up=req.estimated_up_people,
                        actual_down=req.estimated_down_people
                    )
                    print(f"Automatically resolved bidirectional request at floor {req.floor}")
            
            # Process requests and assign elevators
            assignments = await self.coordinator.process_requests_with_reassignment(self.elevators)
            
            # Process new assignments - add destinations to elevators
            if assignments:
                for assignment in assignments:
                    # Find the elevator for this assignment
                    elevator = next((e for e in self.elevators if e.id == assignment.elevator_id), None)
                    if elevator:
                        # Find the batch for this assignment
                        batch = self.coordinator.active_batches.get(assignment.request_id)
                        if batch:
                            # Add the pickup floor as a destination for this elevator
                            elevator.add_destination(batch.floor)
        
            # Process elevator movements
            for elevator in self.elevators:
                if elevator.state == ElevatorState.IDLE and elevator.destination_requests:
                    # Get the next destination
                    next_dest = elevator.destination_requests[0].floor
                    
                    # Skip if already at destination
                    if elevator.current_floor == next_dest:
                        # Remove this destination from the elevator's queue
                        if elevator.destination_requests:
                            elevator.destination_requests.pop(0)
                        continue
                        
                    # Move elevator to the destination
                    await elevator.move_to_floor(next_dest)
                    
                    # Open doors when arrived
                    if elevator.current_floor == next_dest:
                        await elevator.open_doors()
                        
                        # Check if this is a pickup floor
                        pickup_batch = None
                        for batch_id, batch in list(self.coordinator.active_batches.items()):
                            if batch.floor == next_dest and not batch.is_fully_served:
                                pickup_batch = batch
                                break
                        
                        if pickup_batch:
                            # This is a pickup floor - handle passenger boarding
                            capacity = elevator.occupancy_sensor.get_available_capacity()
                            people_to_serve = min(pickup_batch.people_remaining, capacity)
                            
                            # Update batch and elevator
                            pickup_batch.people_served += people_to_serve
                            elevator.occupancy_sensor.update_occupancy(
                                elevator.occupancy_sensor.get_current_occupancy() + people_to_serve
                            )
                            elevator.total_people_served += people_to_serve
                            
                            # Set elevator direction based on the pickup batch direction
                            elevator.direction = pickup_batch.direction
                            
                            # Add passenger destinations (simulate passengers going to random floors)
                            # In a real system, this would come from user input or sensors
                            if pickup_batch.direction == Direction.UP:
                                # Passengers going up will go to higher floors - ensure strictly greater
                                possible_destinations = list(range(next_dest + 1, MAX_FLOOR + 1))
                            else:  # Direction.DOWN:
                                # Passengers going down will go to lower floors - ensure strictly lesser
                                possible_destinations = list(range(MIN_FLOOR, next_dest))
                            
                            if possible_destinations:  # Make sure there are valid destinations
                                # Add 1-3 random destinations for these passengers
                                num_destinations = min(3, len(possible_destinations))
                                destinations = random.sample(possible_destinations, num_destinations)
                                
                                # Track how many people go to each destination
                                people_per_destination = {}
                                remaining_people = people_to_serve
                                
                                # Distribute passengers among destinations
                                for dest in destinations:
                                    # Allocate people to this destination
                                    if dest == destinations[-1]:  # Last destination gets all remaining people
                                        people_per_destination[dest] = remaining_people
                                    else:
                                        # Distribute people somewhat evenly
                                        people_count = max(1, remaining_people // (len(destinations) - destinations.index(dest)))
                                        people_per_destination[dest] = people_count
                                        remaining_people -= people_count
                                    
                                    # Add each destination floor with metadata about passenger count for the elevator
                                    # Store passenger count as a custom attribute in the destination request
                                    elevator.add_destination(dest)
                                    # Store passenger count in the last added destination request
                                    if elevator.destination_requests:
                                        for req in elevator.destination_requests:
                                            if req.floor == dest:
                                                # Add a custom attribute to track passengers for this destination
                                                req.passenger_count = people_per_destination[dest]
                                                break
                        
                        # Close doors
                        await elevator.close_doors()
                        
                        # Remove this destination from the elevator's queue if it was the first one
                        if elevator.destination_requests and elevator.destination_requests[0].floor == next_dest:
                            # Get the destination request
                            dest_request = elevator.destination_requests.pop(0)
                            
                            # If this is a passenger drop-off (not a pickup), update occupancy
                            if hasattr(dest_request, 'passenger_count'):
                                # Get the number of passengers exiting at this floor
                                exiting_passengers = dest_request.passenger_count
                                
                                # Update elevator occupancy
                                current_occupancy = elevator.occupancy_sensor.get_current_occupancy()
                                new_occupancy = max(0, current_occupancy - exiting_passengers)
                                elevator.occupancy_sensor.update_occupancy(new_occupancy)
                                
                                print(f"{exiting_passengers} passengers exited elevator {elevator.id} at floor {next_dest}")
        
            # Small delay between processing cycles
            await asyncio.sleep(1)
    
    def start_system(self):
        """Start the elevator system."""
        if not self.elevators:
            print("Error: Please add at least one elevator first")
            return
        
        if self.running:
            print("System is already running")
            return
        
        print("Starting advanced elevator system...")
        self.running = True
        
        # Start the controller in a separate thread
        def run_controller():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_system())
        
        self.controller_thread = threading.Thread(target=run_controller, daemon=True)
        self.controller_thread.start()
        
        # Start the display thread
        self.display_thread = threading.Thread(target=self._update_display, daemon=True)
        self.display_thread.start()
        
        print("Advanced elevator system started")
    
    def stop_system(self):
        """Stop the elevator system."""
        if not self.running:
            print("System is not running")
            return
        
        print("Stopping advanced elevator system...")
        self.running = False
        print("Advanced elevator system stopped")
    
    def _update_display(self):
        """Periodically update the display with system status."""
        while self.running:
            self.display_status()
            time.sleep(2)  # Update every 2 seconds
    
    def run(self):
        """Run the console UI."""
        print("Welcome to the Advanced Elevator System Console UI")
        print(f"System initialized with {self.total_floors} floors")
        
        while True:
            self.display_menu()
            choice = input("Enter your choice (1-8): ")
            
            if choice == "1":
                self.add_elevator()
            elif choice == "2":
                self.add_floor_request()
            elif choice == "3":
                self.display_status()
            elif choice == "4":
                self.start_system()
            elif choice == "5":
                self.stop_system()
            elif choice == "6":
                self.toggle_maintenance()
            elif choice == "7":
                self.display_metrics()
            elif choice == "8":
                if self.running:
                    self.stop_system()
                print("Exiting advanced elevator system. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    # Create the advanced console UI
    console = AdvancedConsoleUI()
    console.run()
