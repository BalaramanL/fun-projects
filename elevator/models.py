"""
Models module for the Elevator Emulator system.

This module contains the data models and enumerations used throughout the elevator system.
"""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


class ElevatorState(Enum):
    """Represents the possible states of an elevator."""
    IDLE = "IDLE"
    MOVING_UP = "MOVING_UP"
    MOVING_DOWN = "MOVING_DOWN"
    DOOR_OPENING = "DOOR_OPENING"
    DOOR_CLOSING = "DOOR_CLOSING"
    DOOR_OPEN = "DOOR_OPEN"
    DOOR_HELD = "DOOR_HELD"
    MAINTENANCE = "MAINTENANCE"


class Direction(Enum):
    """Represents the possible directions of elevator movement."""
    UP = "UP"
    DOWN = "DOWN"
    NONE = "NONE"


@dataclass
class FloorRequest:
    """
    Represents a request made from a floor to call an elevator.
    
    Attributes:
        floor: The floor number where the request was made
        direction: The intended direction (UP/DOWN)
        people_count: Number of people waiting
        timestamp: When the request was made
        request_id: Unique identifier for the request
    """
    floor: int
    direction: Direction
    people_count: int
    timestamp: datetime
    request_id: str


@dataclass
class DestinationRequest:
    """
    Represents a destination request made from inside an elevator.
    
    Attributes:
        floor: The destination floor
        people_count: Number of people going to this floor
        timestamp: When the request was made
    """
    floor: int
    people_count: int
    timestamp: datetime
