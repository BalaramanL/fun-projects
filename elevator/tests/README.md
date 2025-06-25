# Advanced Elevator System Tests

This directory contains test modules for the Advanced Elevator System. These tests demonstrate the functionality of individual components and the integrated system.

## Test Files

- **components.py**: Component-specific tests for individual elevator system modules
- **systems.py**: Integration tests for the full elevator system

## Running the Tests

### Prerequisites

- Python 3.6+
- All dependencies installed (see main project's `requirements.txt`)
- Activate the virtual environment if you're using one:
  ```bash
  source ../venv/bin/activate  # On macOS/Linux
  ```

### Import Structure

The test files use relative imports to access modules from the parent directory. This is handled by adding the parent directory to the Python path at runtime:

```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

This allows the tests to import modules like `models` and `systems` from the parent directory.

### Component Tests

To run the component-specific tests:

```bash
python components.py
```

This will execute tests for:
- Occupancy Sensor
- Advanced Elevator
- People Distribution Estimator
- Dynamic Elevator Tracker
- Advanced Request Coordinator

### System Tests

To run the integrated system tests:

```bash
python systems.py
```

This will demonstrate:
1. Large request splitting
2. Bi-directional request handling
3. Maintenance resilience
4. Dynamic reassignment

## Understanding Test Output

### Component Tests

When running `components.py`, you'll see output for each component test:

#### Occupancy Sensor Test
- Shows sensor initialization
- Demonstrates occupancy updates
- Verifies capacity calculations

#### Advanced Elevator Test
- Displays elevator movement between floors
- Shows door operations (opening/closing)
- Demonstrates destination management
- Tests maintenance mode

#### People Distribution Estimator Test
- Shows distribution estimates for different floors
- Demonstrates time-of-day based estimations

#### Dynamic Elevator Tracker Test
- Shows elevator tracking initialization
- Demonstrates ETA calculations
- Displays elevator availability updates

#### Advanced Request Coordinator Test
- Shows request creation and assignment
- Demonstrates batch processing
- Displays optimization metrics

### System Tests

When running `systems.py`, you'll see output for each scenario:

#### Scenario 1: Large Request Splitting
- Shows how a large group of people is split across multiple elevators
- Displays elevator assignments and capacities

#### Scenario 2: Bi-directional Request Handling
- Shows how the system handles requests where people want to go both up and down
- Displays estimated and actual distributions

#### Scenario 3: Maintenance Resilience
- Shows how the system adapts when an elevator enters maintenance mode
- Demonstrates reassignment of requests

#### Scenario 4: Dynamic Reassignment
- Shows how long-waiting requests get prioritized
- Demonstrates the system's fairness mechanisms

## Verifying Correct Operation

### Component Tests
- All component tests should complete without errors
- Each test section should show appropriate initialization and state changes
- Occupancy values should always be within capacity limits
- Elevators should move in logical sequences based on their direction

### System Tests
- All scenarios should complete without errors
- Large requests should be properly split across available elevators
- Bi-directional requests should be resolved with appropriate distributions
- When an elevator enters maintenance, its requests should be reassigned
- Long-waiting requests should be prioritized over newer ones

## Troubleshooting

If you encounter issues:

### Import Issues

1. **ModuleNotFoundError**: If you see `ModuleNotFoundError: No module named 'models'` or similar:
   - Ensure you're running the tests from the `tests` directory
   - Verify that the parent directory contains the required modules (`models.py`, `systems.py`, etc.)
   - Check that the import path modification at the top of the test files is working correctly

### Functional Issues

1. **Elevator not moving**: Check if the elevator is in IDLE state or if its destination queue is empty
2. **Request not being processed**: Verify that the request was added to the coordinator
3. **Bidirectional requests not resolving**: Check if the distribution is being properly estimated
4. **Timing issues**: The system uses asyncio; ensure all awaitable functions are properly awaited

### Runtime Errors

1. **AttributeError**: If attributes like `total_people_waiting` are not found, ensure you're using the correct attribute names for each class
2. **KeyError**: When accessing dictionaries like `coordinator.active_batches`, verify that the keys exist before accessing
3. **IndexError**: When accessing lists like `elevator.destination_requests`, check that the list is not empty

## Time and Space Complexity Analysis

### Component Tests
- **Occupancy Sensor**: O(1) time for all operations
- **Advanced Elevator**: O(n) time for destination sorting where n is the number of destinations
- **People Distribution Estimator**: O(1) time for estimations
- **Dynamic Elevator Tracker**: O(e) time for updates where e is the number of elevators
- **Request Coordinator**: O(e*r) time for assignments where e is elevators and r is requests

### System Tests
- **Large Request Splitting**: O(e*r) time where e is elevators and r is requests
- **Bi-directional Handling**: O(e*r) time with O(r) space for tracking distributions
- **Maintenance Resilience**: O(e*r) time for reassignment
- **Dynamic Reassignment**: O(e*r*log(r)) time due to priority-based sorting

## Alternative Testing Approaches

While these tests demonstrate functionality through console output, alternative approaches include:

1. **Unit Tests**: Using pytest or unittest for automated verification
2. **Property-Based Testing**: Using hypothesis to test with random inputs
3. **Simulation Testing**: Running the system with simulated building traffic patterns
4. **Load Testing**: Testing with high volumes of requests to verify scalability

## Contributing New Tests

When adding new tests:

1. Follow the existing pattern of async test functions
2. Add clear print statements to show test progress
3. Include verification steps that confirm correct behavior
4. Document time and space complexity
5. Add the new test to the appropriate test runner function
