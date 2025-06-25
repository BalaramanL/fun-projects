# Advanced Elevator System

A Python-based advanced elevator system with an interactive console interface that simulates the operation of multiple elevators in a building with sophisticated request coordination and optimization.

## Overview

This application simulates a multi-elevator system with the following advanced features:

- Dynamic request coordination with bi-directional request handling
- Real-time elevator availability tracking and service completion time estimation
- Multi-objective optimization for elevator assignments
- Continuous reassignment for improved efficiency
- Intelligent people distribution estimation for bi-directional requests
- Occupancy tracking and capacity management
- Maintenance mode resilience
- Comprehensive system metrics

## Project Structure

The project has been modularized into the following components:

- `models.py`: Core data models and enumerations (Direction, ElevatorState, etc.)
- `systems.py`: Advanced elevator system implementation with request coordination
- `console_ui.py`: Interactive console-based user interface
- `constants.py`: System constants and configuration parameters
- `tests/`: Directory containing component and system tests
  - `components.py`: Component-specific tests
  - `systems.py`: Integration tests for the full system

## Requirements

- Python 3.8 or higher
- asyncio (included with Python)

## Installation

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

- On Windows:
```bash
venv\Scripts\activate
```

- On macOS/Linux:
```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

To run the elevator system with the console UI:

```bash
python console_ui.py
```

## Usage Instructions

The console UI provides an interactive menu with the following options:

1. **Adding Elevators**:
   - Select option 1 from the main menu
   - Enter the starting floor for the elevator
   - At least one elevator is required to start the system

2. **Making Floor Requests**:
   - Select option 2 from the main menu for standard floor requests
   - Select option 3 for bi-directional requests (when people want to go both up and down)
   - Enter the floor number, direction (for standard requests), and number of people waiting

3. **System Control**:
   - Select option 4 to start the system
   - Select option 5 to stop the system
   - Select option 6 to toggle maintenance mode for an elevator

4. **Monitoring**:
   - Select option 7 to display the current system status
   - Select option 8 to show system metrics

5. **Exit**:
   - Select option 9 to exit the application

## Advanced System Features

### Bi-directional Request Handling
The system can handle requests where people at a floor want to go in both directions. It uses intelligent distribution estimation to split these requests appropriately.

### Dynamic Request Coordination
Requests are processed in batches with continuous reassignment to optimize elevator usage and minimize wait times.

### Maintenance Resilience
When an elevator enters maintenance mode, its current and pending requests are automatically reassigned to other available elevators.

### Multi-objective Optimization
Elevator assignments consider multiple factors including:
- Current elevator direction
- Distance to the request floor
- Elevator capacity
- Estimated service completion time

## Component Architecture

For a detailed explanation of the component architecture, including class diagrams and interaction flows, please refer to the [Advanced Elevator System Architecture Document](https://claude.ai/public/artifacts/f6d65aa8-3027-48cc-bfd0-c49e7439a840).

## Technical Details

The system uses:
- `asyncio` for asynchronous operations and concurrent elevator movements
- Object-oriented design with specialized components for different aspects of the system
- Event-driven architecture for request processing and elevator coordination
- Threading to prevent UI freezing during operations

## Extending the System

To extend the system:
- Add new request types by extending the base `FloorRequest` class
- Implement different optimization algorithms in the `AdvancedRequestCoordinator`
- Create specialized elevator types by extending the `AdvancedElevator` class
- Add more sophisticated distribution estimators for different building types

## Future Development Plans

### Graphical User Interface
A modern, interactive GUI is planned for the next version to provide visual representation of elevator movements, floor requests, and system metrics.

### Advanced Analytics
Future versions will include advanced analytics for system performance, including:
- Heat maps of floor activity
- Wait time distribution analysis
- Capacity utilization metrics
- Predictive maintenance scheduling

### Machine Learning Integration
Integration with machine learning models to predict traffic patterns and optimize elevator assignments based on historical data.

### API and External System Integration
REST API endpoints to allow external systems to interact with the elevator system, such as building management systems or mobile applications.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request with improvements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
