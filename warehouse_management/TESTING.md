# Warehouse Management System - Testing Guide

This document provides instructions for testing the Warehouse Management System components independently without having to rebuild the Docker container each time.

## Local Testing Workflow

We've created a script-based workflow that allows you to test each component of the system independently. This is much faster than rebuilding the Docker container each time you make a change.

### Prerequisites

1. **Activate the virtual environment**:

```bash
# Navigate to the warehouse_management folder
cd /path/to/warehouse_management

# Activate the virtual environment
source warehouse/bin/activate  # On Unix/Mac
# OR
.\warehouse\Scripts\activate  # On Windows
```

2. **Ensure all dependencies are installed**:

```bash
pip install -r requirements.txt
```

> **Important**: All commands below assume you have activated the virtual environment. The scripts will not work correctly without the proper Python environment and dependencies.

### Using the Local Test Workflow Script

The script provides several options to test different components of the system:

#### 1. Setup the database only

```bash
python scripts/local_test_workflow.py --setup
```

This will create the database schema and prepare it for data population.

#### 2. Populate the database only

```bash
python scripts/local_test_workflow.py --populate
```

This will populate the database with test data (products, warehouses, customers, orders, inventory, etc.).

#### 3. Run live event simulation only

```bash
python scripts/local_test_workflow.py --simulate
```

This will run the live event simulation for 60 seconds by default. You can specify a custom duration:

```bash
python scripts/local_test_workflow.py --simulate --sim-duration 30
```

#### 4. Run all report generation examples

```bash
python scripts/local_test_workflow.py --report
```

This will run all the report generation examples (reporting_demo, simulation_demo, integration_demo, run_complete_workflow).

#### 5. Run a specific report example

```bash
python scripts/local_test_workflow.py --specific-report reporting_demo
```

Available report examples:
- `reporting_demo` - Tests basic reporting functionality
- `simulation_demo` - Tests simulation-based reporting
- `integration_demo` - Tests integration between simulation and reporting
- `run_complete_workflow` - Tests the complete workflow from simulation to reporting

#### 6. Run the complete workflow

```bash
python scripts/local_test_workflow.py --all
```

This will run all steps in sequence: setup, populate, simulate, and generate reports.

## Recommended Testing Strategy

When fixing issues or making changes to the codebase, follow this testing strategy:

1. First, reset the database and setup the schema:
   ```bash
   python scripts/local_test_workflow.py --setup
   ```

2. Then populate the database with test data:
   ```bash
   python scripts/local_test_workflow.py --populate
   ```

3. Test specific components that you've modified:
   ```bash
   python scripts/local_test_workflow.py --specific-report reporting_demo
   ```

4. If individual components work, test the integration:
   ```bash
   python scripts/local_test_workflow.py --simulate --sim-duration 20
   python scripts/local_test_workflow.py --specific-report integration_demo
   ```

5. Finally, test the complete workflow:
   ```bash
   python scripts/local_test_workflow.py --all
   ```

## Common Issues and Solutions

### 'NoneType' object has no attribute 'quantity'

This error occurs when trying to access the `quantity` attribute of a None object in the order reports module. The fix involves adding defensive checks to handle None values.

### Chart generation errors

These errors occur when the chart output directories are not created correctly or when the chart paths are incorrectly constructed. Make sure the chart directories exist and the paths are correct.

### JSON serialization error

This error occurs when trying to serialize datetime objects to JSON. The fix involves implementing a custom JSON encoder to handle datetime objects.

### Inventory record warnings

The inventory reporting module skips records with None values. This is expected behavior, but if there are too many warnings, it might indicate an issue with the data population or query logic.

## Docker Testing

If you want to test the entire system in a Docker container, you can use the following commands:

```bash
# Build the Docker image
docker build -t warehouse-management -f deployment/Dockerfile .

# Run the Docker container
docker run -it --name warehouse-demo warehouse-management
```

This will run the entire workflow in a Docker container, including database setup, population, simulation, and report generation.
