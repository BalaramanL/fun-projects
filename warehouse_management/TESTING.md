# Warehouse Management System - Testing Guide

This document provides comprehensive instructions for testing the Warehouse Management System components. It covers local testing workflows, example scripts, verification procedures, and Docker-based testing.

## Local Testing Workflow

We've created a script-based workflow that allows you to test each component of the system independently. This is much faster than rebuilding the Docker container each time you make a change.

### Prerequisites

1. **Activate the virtual environment**:

```bash
# Navigate to the warehouse_management folder
cd /path/to/warehouse_management

# Activate the virtual environment
source venv/bin/activate  # On Unix/Mac
# OR
.\venv\Scripts\activate  # On Windows
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

#### 7. Clean output directories

```bash
python scripts/local_test_workflow.py --clean
```

This will clean all output directories while preserving the directory structure.

#### 8. Verify outputs

```bash
python scripts/local_test_workflow.py --verify
```

This will verify that all expected output files have been generated.

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

### 'NoneType' object has no attribute 'quantity' or 'current_stock'

This error occurs when trying to access attributes of a None object in the reporting modules. The fix involves adding defensive checks to handle None values:

```python
# Before accessing attributes, check if the object is None
if inventory_item is not None:
    stock = inventory_item.current_stock
else:
    stock = 0  # Default value
```

### Chart generation errors (cannot convert float NaN to integer)

These errors occur when trying to plot data with NaN values. The fix involves filtering out NaN values before plotting:

```python
# Filter out NaN values before plotting
data = data.dropna()
# Or replace NaN with a default value
data = data.fillna(0)
```

### JSON serialization error with datetime objects

This error occurs when trying to serialize datetime objects to JSON. The fix involves implementing a custom JSON encoder:

```python
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)

# Use the encoder when dumping JSON
json.dumps(data, cls=DateTimeEncoder)
```

### Inventory record warnings

The inventory reporting module skips records with None values. This is expected behavior, but if there are too many warnings, check:

1. Database population scripts to ensure they're creating valid inventory records
2. Query logic to ensure it's joining tables correctly
3. Add more detailed logging to identify which specific records are problematic

### Missing reports or empty reports

If reports are missing or contain only placeholder values:

1. Check that the database has been properly populated
2. Verify that simulation scripts have run successfully
3. Look for errors in the logs that might indicate why data generation failed
4. Run individual report generation functions with debug logging enabled

## Example Scripts

The system includes several example scripts that demonstrate specific functionality:

### 1. Run Example Script

```bash
python scripts/run_example.py
```

This script provides a menu-driven interface to run various examples:
- Basic reporting examples
- Simulation examples
- Integration examples
- Complete workflow examples

### 2. Clean Outputs Script

```bash
python scripts/clean_outputs.py
```

This script cleans all output directories (reports, charts, logs, etc.) while preserving the directory structure. It's useful before running tests to ensure a clean state.

### 3. Verify Outputs Script

```bash
python scripts/verify_outputs.py
```

This script verifies that all expected output files have been generated after running the system. It checks for:
- Report files in various formats
- Chart and plot images
- Log files
- Data export files

## Output Verification Workflow

To ensure the system is working correctly, follow this verification workflow:

1. **Clean all outputs**:
   ```bash
   python scripts/clean_outputs.py
   ```

2. **Run the complete workflow**:
   ```bash
   python scripts/local_test_workflow.py --all
   ```
   Or run specific components as needed.

3. **Verify the outputs**:
   ```bash
   python scripts/verify_outputs.py
   ```

4. **Check for errors in the logs**:
   ```bash
   grep -i "error" outputs/logs/*.log
   ```

## Docker Testing

If you want to test the entire system in a Docker container, you can use the following commands:

```bash
# Build the Docker image
docker build -t warehouse-management -f deployment/Dockerfile .

# Run the Docker container with volume mounts for outputs
docker run -v $(pwd)/outputs:/app/outputs -it --name warehouse-demo warehouse-management
```

This will run the entire workflow in a Docker container, including database setup, population, simulation, and report generation.

### Docker Testing Workflow

1. **Clean outputs before Docker run**:
   ```bash
   python scripts/clean_outputs.py
   ```

2. **Build and run Docker container**:
   ```bash
   docker build -t warehouse-management -f deployment/Dockerfile .
   docker run -v $(pwd)/outputs:/app/outputs -it --name warehouse-demo warehouse-management
   ```

3. **Verify outputs after Docker run**:
   ```bash
   python scripts/verify_outputs.py
   ```

4. **Check Docker logs for errors**:
   ```bash
   docker logs warehouse-demo | grep -i "error"
   ```
