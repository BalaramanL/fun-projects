"""
Advanced Elevator System Implementation
--------------------------------------

This module implements an advanced elevator system with the following key features:
1. Dynamic request coordination with bi-directional request handling
2. Real-time elevator availability tracking and service completion time estimation
3. Multi-objective optimization for elevator assignments
4. Continuous reassignment for improved efficiency
5. Intelligent people distribution estimation for bi-directional requests

Time Complexity: Varies by function, generally O(n) where n is number of elevators or requests
Space Complexity: O(m + n) where m is number of requests and n is number of elevators
"""

import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
import heapq
import uuid
import random
import math

from models import Direction, ElevatorState, FloorRequest, DestinationRequest
from constants import (
    CAPACITY_PER_ELEVATOR, DEFAULT_TOTAL_FLOORS, 
    DOOR_OPEN_TIME, DOOR_OPENING_TIME, DOOR_CLOSING_TIME, FLOOR_TRANSIT_TIME
)

# Define constants not in the constants.py file
MIN_FLOOR = 1
MAX_FLOOR = DEFAULT_TOTAL_FLOORS
DOOR_WAIT_TIME = DOOR_OPEN_TIME  # Use the same value as DOOR_OPEN_TIME
FLOOR_TRAVEL_TIME = FLOOR_TRANSIT_TIME  # Rename for consistency

# Advanced data models for the new system
@dataclass
class BiDirectionalRequest:
    """
    Handles floors where both UP and DOWN buttons are pressed
    
    This model tracks both estimated and actual distributions of people
    waiting to go up or down, allowing the system to make initial assignments
    based on estimates and then refine them once an elevator arrives.
    
    Time Complexity: O(1) for all operations
    Space Complexity: O(1) - fixed size regardless of system scale
    """
    floor: int
    total_people_waiting: int
    estimated_up_people: int
    estimated_down_people: int
    actual_up_people: Optional[int] = None  # Determined when elevator arrives
    actual_down_people: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assigned_elevators: Set[str] = field(default_factory=set)
    
    @property
    def is_distribution_known(self) -> bool:
        """Check if the actual distribution has been determined"""
        return self.actual_up_people is not None and self.actual_down_people is not None
    
    def split_into_directional_requests(self) -> Tuple['FloorRequestBatch', 'FloorRequestBatch']:
        """
        Split into separate UP and DOWN requests once distribution is known
        
        Returns:
            Tuple of UP and DOWN FloorRequestBatch objects
        """
        up_request = FloorRequestBatch(
            floor=self.floor,
            direction=Direction.UP,
            total_people_waiting=self.actual_up_people or self.estimated_up_people,
            timestamp=self.timestamp
        )
        
        down_request = FloorRequestBatch(
            floor=self.floor,
            direction=Direction.DOWN,
            total_people_waiting=self.actual_down_people or self.estimated_down_people,
            timestamp=self.timestamp
        )
        
        return up_request, down_request

@dataclass
class FloorRequestBatch:
    """
    Represents people waiting at a floor in one specific direction
    
    This model tracks a batch of people waiting at a specific floor,
    going in a specific direction. It maintains the state of how many
    people have been served and which elevators are assigned to it.
    
    Time Complexity: O(1) for all operations
    Space Complexity: O(n) where n is the number of assigned elevators
    """
    floor: int
    direction: Direction
    total_people_waiting: int
    people_served: int = 0
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    assigned_elevators: Set[str] = field(default_factory=set)
    priority_score: float = 0.0
    
    @property
    def people_remaining(self) -> int:
        """Calculate how many people are still waiting to be served"""
        return max(0, self.total_people_waiting - self.people_served)
    
    @property
    def is_fully_served(self) -> bool:
        """Check if all people in this batch have been served"""
        return self.people_remaining <= 0
    
    @property
    def wait_time_minutes(self) -> float:
        """Calculate how long this batch has been waiting in minutes"""
        return (datetime.now() - self.timestamp).total_seconds() / 60

@dataclass
class ElevatorAssignment:
    """
    Represents an assignment of an elevator to a specific request
    
    This model tracks the details of an elevator assignment, including
    expected capacity, estimated arrival and completion times, and
    a confidence score for the assignment.
    
    Time Complexity: O(1) for all operations
    Space Complexity: O(1) - fixed size regardless of system scale
    """
    elevator_id: str
    request_id: str
    expected_capacity: int
    estimated_arrival_time: datetime
    estimated_service_completion_time: datetime
    assignment_confidence: float  # How confident we are in this assignment (0-1)


class PeopleDistributionEstimator:
    """
    Estimates UP/DOWN distribution when both buttons are pressed
    
    This class uses historical patterns, time-of-day data, and floor position
    to make intelligent estimates of how many people are going up vs down
    when both buttons are pressed at a floor.
    
    Time Complexity: O(1) for all operations
    Space Complexity: O(n) where n is the number of floors with specific patterns
    """
    
    def __init__(self, total_floors: int = DEFAULT_TOTAL_FLOORS):
        # Historical patterns (could be learned from data)
        self.floor_patterns = {
            # Ground floor: mostly UP
            MIN_FLOOR: {"up_ratio": 0.95, "down_ratio": 0.05},
            # Top floor: mostly DOWN  
            MAX_FLOOR: {"up_ratio": 0.05, "down_ratio": 0.95},
            # Middle floors: depends on time and context
        }
        self.total_floors = total_floors
    
    def estimate_distribution(self, floor: int, total_people: int, 
                           time_of_day: Optional[int] = None) -> Tuple[int, int]:
        """
        Estimate UP vs DOWN distribution for a bi-directional request
        
        Args:
            floor: The floor number
            total_people: Total number of people waiting
            time_of_day: Hour of day (0-23) for time-based patterns
            
        Returns:
            Tuple of (estimated_up_people, estimated_down_people)
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        
        # Use historical patterns if available
        if floor in self.floor_patterns:
            pattern = self.floor_patterns[floor]
            up_people = int(total_people * pattern["up_ratio"])
            down_people = total_people - up_people
            return up_people, down_people
        
        # Default heuristics for middle floors
        if floor <= MIN_FLOOR + 2:  # Lower floors: mostly UP
            up_ratio = 0.7
        elif floor >= MAX_FLOOR - 2:  # Upper floors: mostly DOWN
            up_ratio = 0.3
        else:  # Middle floors: more balanced
            # Calculate position in building (0 = bottom, 1 = top)
            relative_position = (floor - MIN_FLOOR) / (MAX_FLOOR - MIN_FLOOR)
            # Linear interpolation: higher floors have more people going down
            up_ratio = 0.7 - (0.4 * relative_position)  # 0.7 at bottom, 0.3 at top
            
            # Time-based adjustments
            if time_of_day is not None:
                if 7 <= time_of_day <= 10:  # Morning rush: more UP
                    up_ratio = min(0.8, up_ratio + 0.1)
                elif 16 <= time_of_day <= 19:  # Evening rush: more DOWN
                    up_ratio = max(0.2, up_ratio - 0.1)
        
        up_people = int(total_people * up_ratio)
        down_people = total_people - up_people
        
        return up_people, down_people


class DynamicElevatorTracker:
    """
    Tracks elevator availability and estimates service completion times
    
    This class maintains a dynamic model of when each elevator will be
    available, accounting for current passengers, destinations, and
    door operations. It enables intelligent assignment based on
    true availability rather than just current position.
    
    Time Complexity: O(n) where n is the number of destination requests
    Space Complexity: O(n) where n is the number of elevators
    """
    
    def __init__(self):
        self.elevator_schedules: Dict[str, List[Tuple[datetime, str]]] = {}
    
    def calculate_service_completion_time(self, elevator: 'AdvancedElevator') -> datetime:
        """
        Calculate when elevator will be completely free
        
        Args:
            elevator: The elevator to analyze
            
        Returns:
            Datetime when the elevator will be completely free
            
        Time Complexity: O(n) where n is the number of destination requests
        Space Complexity: O(1)
        """
        current_time = datetime.now()
        
        if elevator.state == ElevatorState.IDLE and not elevator.destination_requests:
            return current_time
        
        total_time = 0
        
        # Time for current operation
        if elevator.state == ElevatorState.DOOR_OPENING:
            total_time += DOOR_OPENING_TIME
        elif elevator.state == ElevatorState.DOOR_OPEN:
            # Estimate remaining door open time
            total_time += DOOR_WAIT_TIME / 2  # Assume halfway through wait time
        elif elevator.state == ElevatorState.DOOR_CLOSING:
            total_time += DOOR_CLOSING_TIME
        
        # Time for all destination requests
        current_floor = elevator.current_floor
        
        # Sort destinations by optimal path based on direction
        if elevator.direction == Direction.UP:
            destinations = sorted([req.floor for req in elevator.destination_requests])
        elif elevator.direction == Direction.DOWN:
            destinations = sorted([req.floor for req in elevator.destination_requests], reverse=True)
        else:
            # If IDLE, find optimal path (nearest first)
            destinations = sorted([req.floor for req in elevator.destination_requests], 
                                key=lambda f: abs(current_floor - f))
        
        for dest_floor in destinations:
            # Travel time
            travel_time = abs(current_floor - dest_floor) * FLOOR_TRAVEL_TIME
            # Door operation time
            door_time = DOOR_OPENING_TIME + DOOR_WAIT_TIME + DOOR_CLOSING_TIME
            
            total_time += travel_time + door_time
            current_floor = dest_floor
        
        return current_time + timedelta(seconds=total_time)
    
    def find_next_available_elevator(self, elevators: List['AdvancedElevator'], 
                                   target_floor: int) -> Optional[Tuple['AdvancedElevator', datetime]]:
        """
        Find elevator that will be available soonest for target floor
        
        Args:
            elevators: List of elevators to consider
            target_floor: The floor that needs service
            
        Returns:
            Tuple of (best_elevator, available_time) or None if no elevators available
            
        Time Complexity: O(n*m) where n is number of elevators and m is avg destinations per elevator
        Space Complexity: O(1)
        """
        best_elevator = None
        best_available_time = None
        
        for elevator in elevators:
            if elevator.state == ElevatorState.MAINTENANCE:
                continue
                
            completion_time = self.calculate_service_completion_time(elevator)
            
            # Add travel time from last destination to target floor
            last_floor = elevator.current_floor
            if elevator.destination_requests:
                # Find the last floor the elevator will visit
                if elevator.direction == Direction.UP:
                    last_floor = max([req.floor for req in elevator.destination_requests])
                elif elevator.direction == Direction.DOWN:
                    last_floor = min([req.floor for req in elevator.destination_requests])
                else:  # IDLE or complex path
                    # Use the last destination in the optimal path
                    sorted_dests = sorted([req.floor for req in elevator.destination_requests], 
                                        key=lambda f: abs(elevator.current_floor - f))
                    if sorted_dests:
                        last_floor = sorted_dests[-1]
            
            travel_to_target = abs(last_floor - target_floor) * FLOOR_TRAVEL_TIME
            arrival_at_target = completion_time + timedelta(seconds=travel_to_target)
            
            if best_available_time is None or arrival_at_target < best_available_time:
                best_available_time = arrival_at_target
                best_elevator = elevator
        
        return (best_elevator, best_available_time) if best_elevator else None
    
    def update_elevator_schedule(self, elevator_id: str, completion_time: datetime, status: str):
        """
        Update the schedule for an elevator
        
        Args:
            elevator_id: ID of the elevator
            completion_time: When the elevator will complete its current task
            status: Status description (e.g., 'serving floor 5')
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if elevator_id not in self.elevator_schedules:
            self.elevator_schedules[elevator_id] = []
            
        self.elevator_schedules[elevator_id].append((completion_time, status))
        
        # Clean up old schedule entries
        now = datetime.now()
        self.elevator_schedules[elevator_id] = [
            (time, status) for time, status in self.elevator_schedules[elevator_id]
            if time > now
        ]


class AdvancedRequestCoordinator:
    """
    Enhanced coordinator handling bi-directional requests and dynamic re-assignment
    
    This class is the central orchestration component of the advanced elevator system.
    It manages all request types, coordinates between elevators, and implements
    the multi-objective optimization and dynamic reassignment strategies.
    
    Key features:
    1. Bi-directional request handling with estimation and resolution
    2. Dynamic request reassignment based on changing conditions
    3. Multi-objective optimization for elevator assignments
    4. Continuous monitoring and improvement of system performance
    
    Time Complexity: O(n*m) where n is number of requests and m is number of elevators
    Space Complexity: O(n+m) where n is number of requests and m is number of elevators
    """
    
    def __init__(self):
        self.active_batches: Dict[str, FloorRequestBatch] = {}
        self.bidirectional_requests: Dict[str, BiDirectionalRequest] = {}
        self.estimator = PeopleDistributionEstimator()
        self.tracker = DynamicElevatorTracker()
        self.assignment_queue: List[ElevatorAssignment] = []
        self.reassignment_threshold_seconds = 60  # Reassign if wait time > 60 seconds
        self.wait_time_weight = 10.0  # Weight for wait time in scoring
        self.distance_weight = 1.0   # Weight for distance in scoring
        self.load_weight = 2.0       # Weight for elevator load in scoring
    
    def add_floor_request(self, floor: int, direction: Direction, 
                         people_count: int) -> str:
        """
        Add a new floor request to the system
        
        Args:
            floor: The floor number
            direction: UP, DOWN, or BOTH
            people_count: Number of people waiting
            
        Returns:
            Request ID for tracking
            
        Time Complexity: O(n) where n is number of existing requests
        Space Complexity: O(1)
        """
        # Add Direction.BOTH to the Direction enum if it doesn't exist
        if not hasattr(Direction, "BOTH"):
            Direction.BOTH = "BOTH"
            
        if direction == Direction.BOTH:
            return self._handle_bidirectional_request(floor, people_count)
        else:
            return self._handle_directional_request(floor, direction, people_count)
    
    def _handle_bidirectional_request(self, floor: int, people_count: int) -> str:
        """
        Handle request where both UP and DOWN buttons are pressed
        
        Args:
            floor: The floor number
            people_count: Number of people waiting
            
        Returns:
            Request ID for tracking
            
        Time Complexity: O(n) where n is number of existing bi-directional requests
        Space Complexity: O(1)
        """
        # Check for existing bi-directional request at this floor
        existing = None
        for req in self.bidirectional_requests.values():
            if req.floor == floor and not req.is_distribution_known:
                existing = req
                break
        
        if existing:
            existing.total_people_waiting += people_count
            # Re-estimate distribution
            current_hour = datetime.now().hour
            up_est, down_est = self.estimator.estimate_distribution(
                floor, existing.total_people_waiting, time_of_day=current_hour
            )
            existing.estimated_up_people = up_est
            existing.estimated_down_people = down_est
            return existing.request_id
        else:
            # Create new bi-directional request
            current_hour = datetime.now().hour
            up_est, down_est = self.estimator.estimate_distribution(
                floor, people_count, time_of_day=current_hour
            )
            
            bi_req = BiDirectionalRequest(
                floor=floor,
                total_people_waiting=people_count,
                estimated_up_people=up_est,
                estimated_down_people=down_est
            )
            
            self.bidirectional_requests[bi_req.request_id] = bi_req
            return bi_req.request_id
    
    def _handle_directional_request(self, floor: int, direction: Direction, 
                                  people_count: int) -> str:
        """
        Handle standard directional request
        
        Args:
            floor: The floor number
            direction: UP or DOWN
            people_count: Number of people waiting
            
        Returns:
            Request ID for tracking
            
        Time Complexity: O(n) where n is number of existing batches
        Space Complexity: O(1)
        """
        # Check for existing batch
        existing = self._find_existing_batch(floor, direction)
        
        if existing:
            existing.total_people_waiting += people_count
            return existing.request_id
        else:
            batch = FloorRequestBatch(floor, direction, people_count)
            self.active_batches[batch.request_id] = batch
            return batch.request_id
    
    def _find_existing_batch(self, floor: int, direction: Direction) -> Optional[FloorRequestBatch]:
        """
        Find existing batch for same floor+direction
        
        Args:
            floor: The floor number
            direction: UP or DOWN
            
        Returns:
            Matching FloorRequestBatch or None
            
        Time Complexity: O(n) where n is number of active batches
        Space Complexity: O(1)
        """
        for batch in self.active_batches.values():
            if (batch.floor == floor and 
                batch.direction == direction and 
                not batch.is_fully_served):
                return batch
        return None
    
    async def process_requests_with_reassignment(self, elevators: List['AdvancedElevator']) -> List[ElevatorAssignment]:
        """
        Process requests with dynamic re-assignment capabilities
        
        Args:
            elevators: List of elevators to consider for assignments
            
        Returns:
            List of new elevator assignments
            
        Time Complexity: O(n*m) where n is requests and m is elevators
        Space Complexity: O(n+m)
        """
        # First, handle bi-directional requests that need elevator arrival to resolve
        await self._process_bidirectional_requests(elevators)
        
        # Get all pending directional requests
        pending_batches = [batch for batch in self.active_batches.values() 
                          if not batch.is_fully_served]
        
        # Check for re-assignment opportunities
        await self._check_reassignment_opportunities(pending_batches, elevators)
        
        # Prioritize requests by wait time and people count
        pending_batches.sort(key=lambda b: (
            -b.wait_time_minutes,  # Longer wait = higher priority
            -b.people_remaining    # More people = higher priority
        ))
        
        new_assignments = []
        available_elevators = [e for e in elevators if e.state != ElevatorState.MAINTENANCE]
        
        for batch in pending_batches:
            if not available_elevators:
                break
            
            # Find best assignment strategy
            assignment = self._find_optimal_assignment(batch, available_elevators)
            
            if assignment:
                new_assignments.append(assignment)
                batch.assigned_elevators.add(assignment.elevator_id)
                
                # Remove assigned elevator from available list if it's at capacity
                elevator = next(e for e in elevators if e.id == assignment.elevator_id)
                if elevator.occupancy_sensor.get_available_capacity() <= 0:
                    available_elevators = [e for e in available_elevators 
                                         if e.id != assignment.elevator_id]
        
        return new_assignments
    
    async def _process_bidirectional_requests(self, elevators: List['AdvancedElevator']):
        """
        Send elevators to bi-directional floors to determine actual distribution
        
        Args:
            elevators: List of elevators to consider
            
        Time Complexity: O(n*m) where n is bi-directional requests and m is elevators
        Space Complexity: O(1)
        """
        for bi_req in list(self.bidirectional_requests.values()):
            if bi_req.is_distribution_known:
                # Convert to directional requests
                up_batch, down_batch = bi_req.split_into_directional_requests()
                
                if up_batch.total_people_waiting > 0:
                    self.active_batches[up_batch.request_id] = up_batch
                if down_batch.total_people_waiting > 0:
                    self.active_batches[down_batch.request_id] = down_batch
                
                # Remove bi-directional request
                del self.bidirectional_requests[bi_req.request_id]
            else:
                # Send an elevator to investigate if none assigned yet
                if not bi_req.assigned_elevators:
                    best_elevator = self._find_closest_available_elevator(
                        elevators, bi_req.floor
                    )
                    if best_elevator:
                        # Create investigation assignment
                        travel_time = abs(best_elevator.current_floor - bi_req.floor) * FLOOR_TRAVEL_TIME
                        assignment = ElevatorAssignment(
                            elevator_id=best_elevator.id,
                            request_id=bi_req.request_id,
                            expected_capacity=0,  # Just investigating
                            estimated_arrival_time=datetime.now() + timedelta(seconds=travel_time),
                            estimated_service_completion_time=datetime.now() + timedelta(
                                seconds=travel_time + DOOR_OPENING_TIME + DOOR_WAIT_TIME + DOOR_CLOSING_TIME
                            ),
                            assignment_confidence=0.5  # Medium confidence
                        )
                        bi_req.assigned_elevators.add(best_elevator.id)
                        self.assignment_queue.append(assignment)
    
    async def _check_reassignment_opportunities(self, pending_batches: List[FloorRequestBatch], 
                                              elevators: List['AdvancedElevator']):
        """
        Check if any requests should be reassigned to different elevators
        
        Args:
            pending_batches: List of pending request batches
            elevators: List of elevators to consider
            
        Time Complexity: O(n*m) where n is batches and m is elevators
        Space Complexity: O(1)
        """
        for batch in pending_batches:
            wait_time_seconds = batch.wait_time_minutes * 60
            if wait_time_seconds > self.reassignment_threshold_seconds:
                # Check if there's a better elevator available now
                next_available = self.tracker.find_next_available_elevator(
                    elevators, batch.floor
                )
                
                if next_available:
                    elevator, available_time = next_available
                    
                    # If this elevator can serve much sooner, consider reassignment
                    current_wait = wait_time_seconds
                    estimated_new_wait = (available_time - datetime.now()).total_seconds()
                    
                    if estimated_new_wait < current_wait * 0.7:  # 30% improvement
                        print(f"Reassignment opportunity found for floor {batch.floor}: "
                              f"current wait {current_wait:.1f}s, new wait {estimated_new_wait:.1f}s")
                        
                        # Clear existing assignments and reassign
                        batch.assigned_elevators.clear()
    
    def _find_optimal_assignment(self, batch: FloorRequestBatch, 
                               elevators: List['AdvancedElevator']) -> Optional[ElevatorAssignment]:
        """
        Find optimal elevator assignment using multi-objective optimization
        
        Args:
            batch: The request batch to assign
            elevators: List of elevators to consider
            
        Returns:
            Optimal ElevatorAssignment or None if no suitable elevator
            
        Time Complexity: O(n) where n is number of elevators
        Space Complexity: O(1)
        """
        best_assignment = None
        best_score = float('inf')
        
        for elevator in elevators:
            # Skip if elevator can't accommodate any people
            available_capacity = elevator.occupancy_sensor.get_available_capacity()
            if available_capacity <= 0:
                continue
                
            # Skip if elevator is going in wrong direction and has passengers
            if (elevator.direction != Direction.NONE and 
                elevator.direction != batch.direction and
                elevator.occupancy_sensor.get_current_occupancy() > 0):
                continue
            
            # Calculate comprehensive score
            completion_time = self.tracker.calculate_service_completion_time(elevator)
            travel_time = abs(elevator.current_floor - batch.floor) * FLOOR_TRAVEL_TIME
            arrival_time = completion_time + timedelta(seconds=travel_time)
            
            # Score factors
            wait_factor = (arrival_time - datetime.now()).total_seconds() / 60 * self.wait_time_weight
            distance_factor = abs(elevator.current_floor - batch.floor) * self.distance_weight
            load_factor = elevator.occupancy_sensor.get_current_occupancy() / CAPACITY_PER_ELEVATOR * self.load_weight
            
            # Direction compatibility bonus
            direction_bonus = 0
            if elevator.direction == batch.direction or elevator.direction == Direction.NONE:
                direction_bonus = -2  # Negative score is better
            
            # Penalize elevators that are heavily loaded or far away
            score = wait_factor + distance_factor + load_factor + direction_bonus
            
            if score < best_score:
                best_score = score
                people_to_assign = min(batch.people_remaining, available_capacity)
                best_assignment = ElevatorAssignment(
                    elevator_id=elevator.id,
                    request_id=batch.request_id,
                    expected_capacity=people_to_assign,
                    estimated_arrival_time=arrival_time,
                    estimated_service_completion_time=arrival_time + timedelta(
                        seconds=DOOR_OPENING_TIME + DOOR_WAIT_TIME + DOOR_CLOSING_TIME
                    ),
                    assignment_confidence=0.8
                )
        
        return best_assignment
    
    def _find_closest_available_elevator(self, elevators: List['AdvancedElevator'], 
                                       floor: int) -> Optional['AdvancedElevator']:
        """
        Find closest available elevator
        
        Args:
            elevators: List of elevators to consider
            floor: Target floor
            
        Returns:
            Best elevator or None if none available
            
        Time Complexity: O(n) where n is number of elevators
        Space Complexity: O(1)
        """
        available = [e for e in elevators if e.state != ElevatorState.MAINTENANCE]
        if not available:
            return None
        
        return min(available, key=lambda e: abs(e.current_floor - floor))
    
    def resolve_bidirectional_distribution(self, request_id: str, 
                                         actual_up: int, actual_down: int):
        """
        Called when elevator arrives and determines actual UP/DOWN distribution
        
        Args:
            request_id: ID of the bi-directional request
            actual_up: Actual number of people going up
            actual_down: Actual number of people going down
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if request_id in self.bidirectional_requests:
            bi_req = self.bidirectional_requests[request_id]
            bi_req.actual_up_people = actual_up
            bi_req.actual_down_people = actual_down
            
            print(f"Resolved bi-directional request at floor {bi_req.floor}: "
                  f"{actual_up} UP, {actual_down} DOWN (estimated: "
                  f"{bi_req.estimated_up_people} UP, {bi_req.estimated_down_people} DOWN)")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive system metrics
        
        Returns:
            Dictionary of system metrics
            
        Time Complexity: O(n) where n is number of active requests
        Space Complexity: O(1)
        """
        total_waiting = sum(batch.people_remaining for batch in self.active_batches.values())
        avg_wait_time = 0
        if self.active_batches:
            avg_wait_time = sum(batch.wait_time_minutes for batch in self.active_batches.values()) / len(self.active_batches)
        
        return {
            'total_people_waiting': total_waiting,
            'active_requests': len(self.active_batches),
            'bidirectional_requests': len(self.bidirectional_requests),
            'average_wait_time_minutes': avg_wait_time,
            'requests_over_threshold': len([b for b in self.active_batches.values() 
                                          if b.wait_time_minutes > self.reassignment_threshold_seconds / 60])
        }


class AdvancedElevator:
    """
    Enhanced elevator with improved state management and request handling
    
    This class extends the basic elevator functionality with advanced features
    like maintenance resilience, bi-directional request handling, and
    improved occupancy tracking.
    
    Time Complexity: O(1) for most operations, O(n) for path planning
    Space Complexity: O(n) where n is the number of destination requests
    """
    
    def __init__(self, elevator_id: str, total_floors: int = DEFAULT_TOTAL_FLOORS, 
                 current_floor: int = MIN_FLOOR):
        self.id = elevator_id
        self.current_floor = current_floor
        self.state = ElevatorState.IDLE
        self.direction = Direction.NONE
        self.destination_requests: List[DestinationRequest] = []
        self.occupancy_sensor = OccupancySensor()
        self.total_floors = total_floors
        self.maintenance_mode = False
        self.door_open = False
        
        # Performance metrics
        self.total_trips = 0
        self.total_floors_traveled = 0
        self.total_people_served = 0
        self.idle_time_seconds = 0
        self.last_state_change = datetime.now()
    
    async def move_to_floor(self, floor: int):
        """
        Move elevator to target floor
        
        Args:
            floor: Target floor number
            
        Time Complexity: O(n) where n is the number of floors to travel
        Space Complexity: O(1)
        """
        if self.state == ElevatorState.MAINTENANCE:
            print(f"Elevator {self.id} is in maintenance mode, cannot move")
            return
            
        if floor < MIN_FLOOR or floor > MAX_FLOOR:
            print(f"Invalid floor {floor}, must be between {MIN_FLOOR} and {MAX_FLOOR}")
            return
            
        if floor == self.current_floor:
            return
            
        # Set direction based on target floor
        old_direction = self.direction
        self.direction = Direction.UP if floor > self.current_floor else Direction.DOWN
        
        # Update state
        old_state = self.state
        self.state = ElevatorState.MOVING_UP if self.direction == Direction.UP else ElevatorState.MOVING_DOWN
        self._update_metrics(old_state)
        
        # Calculate travel time
        floors_to_travel = abs(floor - self.current_floor)
        travel_time = floors_to_travel * FLOOR_TRAVEL_TIME
        
        print(f"Elevator {self.id} moving from floor {self.current_floor} "
              f"to floor {floor} ({self.direction.name})")
        
        await asyncio.sleep(travel_time)
        
        # Update position and metrics
        self.total_floors_traveled += floors_to_travel
        self.current_floor = floor
        
        # If no more destinations in current direction, become idle
        if not self._has_destinations_in_direction(self.direction):
            self.direction = Direction.NONE
            old_state = self.state
            self.state = ElevatorState.IDLE
            self._update_metrics(old_state)
    
    async def open_doors(self):
        """
        Open elevator doors
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if self.door_open:
            return
            
        old_state = self.state
        self.state = ElevatorState.DOOR_OPENING
        self._update_metrics(old_state)
        
        print(f"Elevator {self.id} opening doors at floor {self.current_floor}")
        await asyncio.sleep(DOOR_OPENING_TIME)
        
        self.door_open = True
        old_state = self.state
        self.state = ElevatorState.DOOR_OPEN
        self._update_metrics(old_state)
    
    async def close_doors(self):
        """
        Close elevator doors
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if not self.door_open:
            return
            
        # Wait for passengers to finish entering/exiting
        await asyncio.sleep(DOOR_WAIT_TIME)
        
        old_state = self.state
        self.state = ElevatorState.DOOR_CLOSING
        self._update_metrics(old_state)
        
        print(f"Elevator {self.id} closing doors at floor {self.current_floor}")
        await asyncio.sleep(DOOR_CLOSING_TIME)
        
        self.door_open = False
        old_state = self.state
        self.state = ElevatorState.IDLE
        self._update_metrics(old_state)
    
    def add_destination(self, floor: int):
        """
        Add a destination floor to the elevator's queue
        
        Args:
            floor: The floor to add as a destination
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if self.state == ElevatorState.MAINTENANCE:
            print(f"Elevator {self.id} is in maintenance mode, cannot add destination")
            return
            
        if floor < MIN_FLOOR or floor > MAX_FLOOR:
            print(f"Invalid floor {floor}, must be between {MIN_FLOOR} and {MAX_FLOOR}")
            return
            
        if floor == self.current_floor:
            return
            
        # Create a destination request
        request = DestinationRequest(
            floor=floor,
            people_count=1,  # Default to 1 person for simplicity
            timestamp=datetime.now()
        )
        
        # Add to destination requests and sort them in order of travel
        self.destination_requests.append(request)
        
        # Sort destinations by floor number based on elevator direction
        if self.direction == Direction.UP:
            # When going up, visit lower floors first
            self.destination_requests.sort(key=lambda r: r.floor)
        elif self.direction == Direction.DOWN:
            # When going down, visit higher floors first
            self.destination_requests.sort(key=lambda r: r.floor, reverse=True)
        
        # Update direction if currently idle
        if self.state == ElevatorState.IDLE and self.direction == Direction.NONE:
            self.direction = Direction.UP if floor > self.current_floor else Direction.DOWN
            # Sort after setting direction
            if self.direction == Direction.UP:
                self.destination_requests.sort(key=lambda r: r.floor)
            else:  # Direction.DOWN
                self.destination_requests.sort(key=lambda r: r.floor, reverse=True)
        
        print(f"Added destination {floor} to elevator {self.id}")
    
    def update_occupancy(self, delta: int):
        """
        Update elevator occupancy
        
        Args:
            delta: Change in occupancy (positive = people entering, negative = exiting)
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        current = self.occupancy_sensor.get_current_occupancy()
        new_occupancy = current + delta
        
        if new_occupancy < 0:
            print(f"Warning: Occupancy would be negative ({new_occupancy}), setting to 0")
            new_occupancy = 0
        elif new_occupancy > CAPACITY_PER_ELEVATOR:
            print(f"Warning: Occupancy would exceed capacity ({new_occupancy} > {CAPACITY_PER_ELEVATOR}), "
                  f"setting to {CAPACITY_PER_ELEVATOR}")
            new_occupancy = CAPACITY_PER_ELEVATOR
        
        self.occupancy_sensor.update_occupancy(new_occupancy)
        print(f"Elevator {self.id} occupancy updated: {current} -> {new_occupancy}")
        
        if delta > 0:  # People entered
            self.total_people_served += delta
    
    def add_destination_request(self, request: DestinationRequest):
        """
        Add a new destination request
        
        Args:
            request: The destination request to add
            
        Time Complexity: O(n) where n is the number of existing requests
        Space Complexity: O(1)
        """
        # Check if request already exists
        for existing in self.destination_requests:
            if existing.floor == request.floor:
                return
                
        self.destination_requests.append(request)
        
        # Update direction if currently NONE
        if self.direction == Direction.NONE and self.state == ElevatorState.IDLE:
            if request.floor > self.current_floor:
                self.direction = Direction.UP
            elif request.floor < self.current_floor:
                self.direction = Direction.DOWN
    
    def remove_destination_request(self, floor: int):
        """
        Remove a destination request for a specific floor
        
        Args:
            floor: The floor to remove from destinations
            
        Time Complexity: O(n) where n is the number of destination requests
        Space Complexity: O(1)
        """
        self.destination_requests = [req for req in self.destination_requests if req.floor != floor]
    
    def get_next_destination(self) -> Optional[int]:
        """
        Get the next optimal destination based on current direction
        
        Returns:
            Next destination floor or None if no destinations
            
        Time Complexity: O(n) where n is the number of destination requests
        Space Complexity: O(1)
        """
        if not self.destination_requests:
            return None
            
        # If we have a direction, prioritize requests in that direction
        if self.direction == Direction.UP:
            # Find closest floor above current floor
            candidates = [req.floor for req in self.destination_requests 
                         if req.floor > self.current_floor]
            if candidates:
                return min(candidates)
                
            # If no floors above, reverse direction and find highest floor below
            candidates = [req.floor for req in self.destination_requests 
                         if req.floor < self.current_floor]
            if candidates:
                return max(candidates)
                
        elif self.direction == Direction.DOWN:
            # Find closest floor below current floor
            candidates = [req.floor for req in self.destination_requests 
                         if req.floor < self.current_floor]
            if candidates:
                return max(candidates)
                
            # If no floors below, reverse direction and find lowest floor above
            candidates = [req.floor for req in self.destination_requests 
                         if req.floor > self.current_floor]
            if candidates:
                return min(candidates)
        
        # If no direction or no floors in current direction, find nearest floor
        return min(self.destination_requests, key=lambda req: abs(req.floor - self.current_floor)).floor
    
    def enter_maintenance_mode(self):
        """
        Put elevator in maintenance mode
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        old_state = self.state
        self.state = ElevatorState.MAINTENANCE
        self._update_metrics(old_state)
        self.maintenance_mode = True
        print(f"Elevator {self.id} entered maintenance mode")
    
    def exit_maintenance_mode(self):
        """
        Exit maintenance mode
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if self.state != ElevatorState.MAINTENANCE:
            return
            
        old_state = self.state
        self.state = ElevatorState.IDLE
        self._update_metrics(old_state)
        self.maintenance_mode = False
        self.direction = Direction.NONE
        print(f"Elevator {self.id} exited maintenance mode")
    
    def _has_destinations_in_direction(self, direction: Direction) -> bool:
        """
        Check if there are destinations in the specified direction
        
        Args:
            direction: Direction to check
            
        Returns:
            True if destinations exist in that direction
            
        Time Complexity: O(n) where n is the number of destination requests
        Space Complexity: O(1)
        """
        if direction == Direction.UP:
            return any(req.floor > self.current_floor for req in self.destination_requests)
        elif direction == Direction.DOWN:
            return any(req.floor < self.current_floor for req in self.destination_requests)
        else:
            return False
    
    async def move_to_next_floor(self):
        """
        Move elevator one floor in the current direction
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if self.state == ElevatorState.MAINTENANCE:
            print(f"Elevator {self.id} is in maintenance mode, cannot move")
            return
            
        if self.direction == Direction.NONE:
            if self.destination_requests:
                # Determine direction based on first destination
                next_floor = self.destination_requests[0].floor
                self.direction = Direction.UP if next_floor > self.current_floor else Direction.DOWN
            else:
                print(f"Elevator {self.id} has no destinations, staying at floor {self.current_floor}")
                return
        
        # Update state
        old_state = self.state
        self.state = ElevatorState.MOVING_UP if self.direction == Direction.UP else ElevatorState.MOVING_DOWN
        self._update_metrics(old_state)
        
        # Move one floor in current direction
        target_floor = self.current_floor + (1 if self.direction == Direction.UP else -1)
        
        # Check if target floor is valid
        if target_floor < MIN_FLOOR or target_floor > MAX_FLOOR:
            print(f"Cannot move {self.direction.name} from floor {self.current_floor}")
            self.direction = Direction.NONE
            old_state = self.state
            self.state = ElevatorState.IDLE
            self._update_metrics(old_state)
            return
        
        # Move to next floor
        print(f"Elevator {self.id} moving from floor {self.current_floor} "
              f"to floor {target_floor} ({self.direction.name})")
        
        await asyncio.sleep(FLOOR_TRAVEL_TIME)
        
        # Update position and metrics
        self.total_floors_traveled += 1
        self.current_floor = target_floor
        
        # Check if we've reached a destination
        self._check_reached_destination()
    
    def _check_reached_destination(self):
        """
        Check if the elevator has reached any of its destinations
        and remove them from the queue
        
        Time Complexity: O(n) where n is the number of destination requests
        Space Complexity: O(1)
        """
        # Find destinations that match current floor
        reached_destinations = [req for req in self.destination_requests 
                               if req.floor == self.current_floor]
        
        if reached_destinations:
            # Remove reached destinations
            self.destination_requests = [req for req in self.destination_requests 
                                        if req.floor != self.current_floor]
            
            # Update metrics
            self.total_trips += len(reached_destinations)
            
            # If no more destinations, become idle
            if not self.destination_requests:
                self.direction = Direction.NONE
                old_state = self.state
                self.state = ElevatorState.IDLE
                self._update_metrics(old_state)
                print(f"Elevator {self.id} has no more destinations, becoming idle")
            # If no more destinations in current direction, check if we need to change direction
            elif not self._has_destinations_in_direction(self.direction):
                # Change direction if there are destinations in the other direction
                opposite_direction = Direction.DOWN if self.direction == Direction.UP else Direction.UP
                if self._has_destinations_in_direction(opposite_direction):
                    self.direction = opposite_direction
                    print(f"Elevator {self.id} changing direction to {self.direction.name}")
                else:
                    self.direction = Direction.NONE
                    old_state = self.state
                    self.state = ElevatorState.IDLE
                    self._update_metrics(old_state)
    
    def _update_metrics(self, old_state: ElevatorState):
        """
        Update performance metrics on state change
        
        Args:
            old_state: Previous elevator state
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        now = datetime.now()
        time_in_state = (now - self.last_state_change).total_seconds()
        
        if old_state == ElevatorState.IDLE:
            self.idle_time_seconds += time_in_state
        
        self.last_state_change = now
        
        # Count completed trips when transitioning to IDLE after serving a floor
        if (old_state in [ElevatorState.DOOR_CLOSING, ElevatorState.DOOR_OPEN] and 
            self.state == ElevatorState.IDLE):
            self.total_trips += 1


class OccupancySensor:
    """
    Tracks elevator occupancy
    
    Time Complexity: O(1) for all operations
    Space Complexity: O(1)
    """
    
    def __init__(self):
        self.current_occupancy = 0
    
    def update_occupancy(self, new_occupancy: int):
        """
        Update current occupancy
        
        Args:
            new_occupancy: New occupancy count
        """
        self.current_occupancy = new_occupancy
    
    def get_current_occupancy(self) -> int:
        """
        Get current occupancy
        
        Returns:
            Current number of people in elevator
        """
        return self.current_occupancy
    
    def get_available_capacity(self) -> int:
        """
        Get available capacity
        
        Returns:
            Number of additional people the elevator can accommodate
        """
        return max(0, CAPACITY_PER_ELEVATOR - self.current_occupancy)


# Demo code moved to tests/systems.py
