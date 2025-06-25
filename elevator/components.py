"""
Core components module for the Elevator Emulator system.

This module contains the core components like OccupancySensor, Elevator, Floor, etc.
"""
import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from models import ElevatorState, Direction, FloorRequest, DestinationRequest


class OccupancySensor:
    """
    Sensor that tracks the current occupancy of an elevator.
    
    Attributes:
        current_occupancy: Current number of people in the elevator
        max_capacity: Maximum capacity of the elevator
    """
    def __init__(self):
        """Initialize the occupancy sensor."""
        from constants import CAPACITY_PER_ELEVATOR
        self.max_capacity = CAPACITY_PER_ELEVATOR
        self.current_occupancy = 0
    
    def update_occupancy(self, people_in: int, people_out: int):
        """
        Update the occupancy based on people entering and exiting.
        
        Args:
            people_in: Number of people entering the elevator
            people_out: Number of people exiting the elevator
        """
        self.current_occupancy = max(0, min(self.max_capacity, 
                                          self.current_occupancy + people_in - people_out))
    
    def get_current_occupancy(self) -> int:
        """Get the current number of people in the elevator."""
        return self.current_occupancy
    
    def get_available_capacity(self) -> int:
        """Get the remaining capacity of the elevator."""
        return self.max_capacity - self.current_occupancy
    
    def can_accommodate(self, people_count: int) -> bool:
        """Check if the elevator can accommodate the given number of people."""
        return self.current_occupancy + people_count <= self.max_capacity


class Elevator:
    """
    Represents an elevator in the system.
    
    Attributes:
        id: Unique identifier for the elevator
        current_floor: The floor where the elevator currently is
        state: Current state of the elevator
        direction: Current direction of movement
        occupancy_sensor: Sensor tracking occupancy
        destination_requests: List of destination requests
        total_movement_cost: Counter for maintenance tracking
        maintenance_until: Timestamp when maintenance ends
        door_held_since: Timestamp when door was held open
        last_update: Timestamp of last update
    """
    def __init__(self, elevator_id: str):
        self.id = elevator_id
        self.current_floor = 1
        self.state = ElevatorState.IDLE
        self.direction = Direction.NONE
        self.last_direction = Direction.NONE  # Track last direction for better decision making
        self.occupancy_sensor = OccupancySensor()
        self.destination_requests: List[DestinationRequest] = []
        self.pending_requests = []  # Track floor requests assigned to this elevator
        self.total_movement_cost = 0
        self.maintenance_until: Optional[datetime] = None
        self.door_held_since: Optional[datetime] = None
        self.last_update = datetime.now()
    
    async def move_to_floor(self, target_floor: int):
        """
        Move the elevator to the specified floor.
        
        Args:
            target_floor: The floor to move to
            
        This method handles:
        1. Checking if the target floor is valid
        2. Moving the elevator floor by floor
        3. Updating costs and checking for maintenance threshold
        4. Simulating transit time between floors
        
        Time Complexity: O(n) where n is the number of floors to travel
        Space Complexity: O(1)
        """
        from constants import FLOOR_TRANSIT_TIME, FLOOR_TRANSIT_COST, MAXIMUM_COST_UNTIL_MAINTENANCE, DEFAULT_TOTAL_FLOORS
        
        # Validate target floor is within bounds
        if target_floor < 1 or target_floor > DEFAULT_TOTAL_FLOORS:
            print(f"Warning: Invalid floor {target_floor}. Valid range is 1-{DEFAULT_TOTAL_FLOORS}")
            return
            
        if self.state == ElevatorState.MAINTENANCE:
            print(f"Elevator {self.id} is in maintenance and cannot move")
            return
        
        if target_floor == self.current_floor:
            return
        
        # Set direction based on target floor
        direction = Direction.UP if target_floor > self.current_floor else Direction.DOWN
        self.direction = direction
        self.last_direction = direction  # Update last_direction when moving
        self.state = ElevatorState.MOVING_UP if direction == Direction.UP else ElevatorState.MOVING_DOWN
        
        # Move floor by floor until reaching target
        while self.current_floor != target_floor:
            # Move one floor in the appropriate direction
            if direction == Direction.UP:
                self.current_floor += 1
            else:  # Direction.DOWN
                self.current_floor -= 1
                
            # Update cost and check for maintenance
            self.total_movement_cost += FLOOR_TRANSIT_COST
            if self.total_movement_cost >= MAXIMUM_COST_UNTIL_MAINTENANCE:
                print(f"Elevator {self.id} has reached maximum cost threshold ({self.total_movement_cost}/{MAXIMUM_COST_UNTIL_MAINTENANCE})")
                await self.enter_maintenance()
                return
                
            # Simulate time taken to move between floors
            await asyncio.sleep(FLOOR_TRANSIT_TIME)
            
        # Update state after reaching the target floor
        if self.state != ElevatorState.MAINTENANCE:  # Only update if not in maintenance
            # If there are passengers or destination requests, maintain direction
            if self.occupancy_sensor.get_current_occupancy() > 0:
                # Keep the current moving state if there are passengers
                pass  # State already set correctly above
            elif self.destination_requests:
                # If there are more destinations, determine direction based on next destination
                next_dest = self.get_next_destination()
                if next_dest is not None:
                    if next_dest > self.current_floor:
                        self.direction = Direction.UP
                        self.state = ElevatorState.MOVING_UP
                        self.last_direction = Direction.UP
                    elif next_dest < self.current_floor:
                        self.direction = Direction.DOWN
                        self.state = ElevatorState.MOVING_DOWN
                        self.last_direction = Direction.DOWN
                    else:
                        # This shouldn't happen, but just in case
                        self.state = ElevatorState.IDLE
                        self.direction = Direction.NONE
                if next_dest > self.current_floor:
                    self.direction = Direction.UP
                    self.state = ElevatorState.MOVING_UP
                    self.last_direction = Direction.UP
                elif next_dest < self.current_floor:
                    self.direction = Direction.DOWN
                    self.state = ElevatorState.MOVING_DOWN
                    self.last_direction = Direction.DOWN
                else:
                    # This shouldn't happen, but just in case
                    self.state = ElevatorState.IDLE
                    self.direction = Direction.NONE
            else:
                # No more destinations
                self.state = ElevatorState.IDLE
                self.direction = Direction.NONE
        else:
            # No passengers and no destinations
            self.state = ElevatorState.IDLE
            self.direction = Direction.NONE
    
    async def enter_maintenance(self):
        """Put the elevator in maintenance mode."""
        from constants import MAINTENANCE_PERIOD
        
        print(f"Elevator {self.id} entering maintenance mode")
        self.state = ElevatorState.MAINTENANCE
        
        # Reset movement cost
        self.total_movement_cost = 0
        
        # Wait for maintenance to complete
        await asyncio.sleep(MAINTENANCE_PERIOD)  # Maintenance period from constants
        
        # Return to service
        self.state = ElevatorState.IDLE
        self.direction = Direction.NONE
        print(f"Elevator {self.id} back in service")
    
    def is_under_maintenance(self) -> bool:
        """Check if the elevator is currently under maintenance."""
        if self.maintenance_until and datetime.now() >= self.maintenance_until:
            self.exit_maintenance()
        return self.state == ElevatorState.MAINTENANCE
    
    def exit_maintenance(self):
        """Exit maintenance mode if the elevator is in maintenance."""
        if self.state == ElevatorState.MAINTENANCE:
            self.state = ElevatorState.IDLE
            self.total_movement_cost = 0
            self.maintenance_until = None
            print(f"Elevator {self.id} back in service")
    
    async def open_door(self):
        """Open the elevator door."""
        from constants import DOOR_OPENING_TIME, DOOR_OPEN_TIME
        
        if self.state == ElevatorState.MAINTENANCE:
            return
        
        self.state = ElevatorState.DOOR_OPENING
        await asyncio.sleep(DOOR_OPENING_TIME)  # Door opening time from constants
        
        self.state = ElevatorState.DOOR_OPEN
        self.door_held_since = time.time()
        
        # Door stays open for specified time
        await asyncio.sleep(DOOR_OPEN_TIME)  # 5 seconds wait time
        
        # Check if door is held
        if self.door_held_since:
            self.state = ElevatorState.DOOR_HELD
            # Alarm after 1 minute
            if time.time() - self.door_held_since > 60:
                self.door_held_since = None
                print(f"Elevator {self.id} door alarm - forcing close")
        
        await self.close_door()
    
    async def close_door(self):
        """Close the elevator door."""
        from constants import DOOR_CLOSING_TIME
        
        if self.state != ElevatorState.DOOR_OPEN:
            return
        
        self.state = ElevatorState.DOOR_CLOSING
        await asyncio.sleep(DOOR_CLOSING_TIME)  # Door closing time from constants
        
        # Check if there are people in the elevator or destination requests
        if self.occupancy_sensor.get_current_occupancy() > 0:
            # If there are people, maintain the last direction
            if self.last_direction == Direction.UP:
                self.state = ElevatorState.MOVING_UP
                self.direction = Direction.UP
            elif self.last_direction == Direction.DOWN:
                self.state = ElevatorState.MOVING_DOWN
                self.direction = Direction.DOWN
            else:
                # If no last direction but people are inside, default to IDLE
                # The controller will assign a destination
                self.state = ElevatorState.IDLE
        elif self.destination_requests:
            # If there are destination requests but no people, we're likely
            # responding to a floor request - keep moving
            next_floor = self.get_next_destination()
            if next_floor and next_floor > self.current_floor:
                self.state = ElevatorState.MOVING_UP
                self.direction = Direction.UP
                self.last_direction = Direction.UP
            elif next_floor and next_floor < self.current_floor:
                self.state = ElevatorState.MOVING_DOWN
                self.direction = Direction.DOWN
                self.last_direction = Direction.DOWN
            else:
                self.state = ElevatorState.IDLE
                self.direction = Direction.NONE
        else:
            # No people and no destinations
            self.state = ElevatorState.IDLE
            self.direction = Direction.NONE
            
        self.door_held_since = None
    
    def add_destination_request(self, floor: int, people_count: int):
        """
        Add a destination request to the elevator.
        
        Args:
            floor: The destination floor
            people_count: Number of people going to this floor
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        from constants import DEFAULT_TOTAL_FLOORS
        
        # Validate floor bounds
        if floor < 1 or floor > DEFAULT_TOTAL_FLOORS:
            print(f"Warning: Cannot add destination to invalid floor {floor}. Valid range is 1-{DEFAULT_TOTAL_FLOORS}")
            return
            
        # Check if there's already a request for this floor
        for req in self.destination_requests:
            if req.floor == floor:
                # Update existing request with additional people
                req.people_count += people_count
                print(f"Updated existing destination request for floor {floor}, now {req.people_count} people")
                return
                
        # Create new request if none exists
        request = DestinationRequest(floor, people_count, datetime.now())
        self.destination_requests.append(request)
        print(f"Added new destination request for floor {floor} with {people_count} people")
        
    def add_destination(self, request: DestinationRequest):
        """
        Add a destination request object to the elevator.
        
        Args:
            request: The DestinationRequest object to add
            
        Time Complexity: O(n) where n is the number of existing destination requests
        Space Complexity: O(1)
        """
        from constants import DEFAULT_TOTAL_FLOORS
        
        # Validate floor bounds
        if request.floor < 1 or request.floor > DEFAULT_TOTAL_FLOORS:
            print(f"Warning: Cannot add destination to invalid floor {request.floor}. Valid range is 1-{DEFAULT_TOTAL_FLOORS}")
            return
            
        # Check if there's already a request for this floor
        for req in self.destination_requests:
            if req.floor == request.floor:
                # Update existing request with additional people
                req.people_count += request.people_count
                print(f"Updated existing destination request for floor {request.floor}, now {req.people_count} people")
                return
                
        # Add new request if none exists
        self.destination_requests.append(request)
        print(f"Added destination request for floor {request.floor} with {request.people_count} people")
    
    def get_next_destination(self) -> Optional[int]:
        """
        Get the next destination floor based on current requests and direction.
        
        Returns:
            The next floor to visit or None if no destinations
        """
        if not self.destination_requests:
            return None
        
        # Sort by floor number based on current direction
        if self.direction == Direction.UP:
            # First try to find destinations above current floor
            next_dest = min([req for req in self.destination_requests 
                           if req.floor > self.current_floor], 
                          key=lambda x: x.floor, default=None)
            
            # If no destinations above, change direction and find one below
            if not next_dest:
                next_dest = max([req for req in self.destination_requests], 
                              key=lambda x: x.floor, default=None)
                
        elif self.direction == Direction.DOWN:
            # First try to find destinations below current floor
            next_dest = max([req for req in self.destination_requests 
                           if req.floor < self.current_floor], 
                          key=lambda x: x.floor, default=None)
            
            # If no destinations below, change direction and find one above
            if not next_dest:
                next_dest = min([req for req in self.destination_requests], 
                              key=lambda x: x.floor, default=None)
        else:
            # If no direction, choose closest destination
            next_dest = min(self.destination_requests, key=lambda x: abs(x.floor - self.current_floor))
        
        if next_dest:
            self.destination_requests.remove(next_dest)
            return next_dest.floor
        return None


class Floor:
    """
    Represents a floor in the building.
    
    Attributes:
        number: Floor number
        up_requests: List of requests to go up
        down_requests: List of requests to go down
        has_up_button: Whether this floor has an up button
        has_down_button: Whether this floor has a down button
        people_waiting_up: Number of people waiting to go up
        people_waiting_down: Number of people waiting to go down
    """
    def __init__(self, floor_number: int, total_floors: int):
        self.number = floor_number
        self.up_requests: List[FloorRequest] = []
        self.down_requests: List[FloorRequest] = []
        self.has_up_button = floor_number < total_floors
        self.has_down_button = floor_number > 1
        self.people_waiting_up = 0
        self.people_waiting_down = 0
    
    def add_request(self, direction: Direction, people_count: int) -> str:
        """
        Add a request from this floor.
        
        Args:
            direction: Direction of the request (UP/DOWN)
            people_count: Number of people making the request
            
        Returns:
            Unique ID for the request
        """
        request_id = f"req_{self.number}_{direction.value}_{datetime.now().timestamp()}"
        request = FloorRequest(self.number, direction, people_count, datetime.now(), request_id)
        
        if direction == Direction.UP and self.has_up_button:
            self.up_requests.append(request)
            self.people_waiting_up += people_count
        elif direction == Direction.DOWN and self.has_down_button:
            self.down_requests.append(request)
            self.people_waiting_down += people_count
        
        return request_id
    
    def get_pending_requests(self) -> List[FloorRequest]:
        """Get all pending requests from this floor."""
        return self.up_requests + self.down_requests
    
    def remove_request(self, request_id: str):
        """
        Remove a request that has been served.
        
        Args:
            request_id: ID of the request to remove
        """
        self.up_requests = [req for req in self.up_requests if req.request_id != request_id]
        self.down_requests = [req for req in self.down_requests if req.request_id != request_id]
        
        # Recalculate waiting people
        self.people_waiting_up = sum(req.people_count for req in self.up_requests)
        self.people_waiting_down = sum(req.people_count for req in self.down_requests)
