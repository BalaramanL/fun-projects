# Warehouse Management System (Proof of Concept)

A comprehensive warehouse management system for optimizing inventory, delivery, and warehouse operations. This proof of concept demonstrates intelligent warehouse management with real-time analytics, predictive alerts, and optimization algorithms. It can be applied to various retail and delivery operations (such as online grocery services like BlinkIt) and customized for different locations (such as Bangalore or any other region).

## Features

- **Smart Alert System**: Stock depletion warnings, high-demand product identification, unusual pattern detection
- **Demand Forecasting**: Time-series analysis, area-wise demand patterns, product lifecycle predictions
- **Optimization Algorithms**: TSP solver for routes, dynamic staffing, inventory balancing
- **Real-time Event Simulation**: Queue-based event generation with realistic purchase patterns
- **Comprehensive Reporting**: Console-based metrics and HTML visualizations

## Project Structure

```
warehouse_management/
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── deployment/                # Deployment configurations
│   └── Dockerfile             # Docker container definition
├── scripts/                   # Executable scripts
│   ├── setup_database.py      # Database initialization
│   ├── populate_products.py   # Product data generation
│   ├── populate_warehouses.py # Warehouse data generation
│   ├── populate_inventory.py  # Inventory data generation
│   ├── populate_customers_orders.py # Customer and order data generation
│   ├── run_all_setup.py       # Run all setup scripts in sequence
│   ├── simulate_live_events.py # Simulate real-time purchase events
│   └── generate_reports.py    # Report generation
├── src/                       # Source code
│   ├── config/                # Configuration files
│   ├── models/                # Data models
│   ├── services/              # Business logic services
│   ├── utils/                 # Utility functions
│   ├── reports/               # Reporting modules
│   └── core/                  # Core application logic
├── tests/                     # Test suite
├── data/                      # Data storage
└── outputs/                   # Generated outputs
```

## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure as needed
6. Initialize the database: `python scripts/setup_database.py`
7. Populate all sample data: `python scripts/run_all_setup.py`
   - Or run individual population scripts:
     - `python scripts/populate_products.py`
     - `python scripts/populate_warehouses.py`
     - `python scripts/populate_inventory.py`
     - `python scripts/populate_customers_orders.py`
8. Simulate live events (optional): `python scripts/simulate_live_events.py --events-per-minute 10`

## Usage

### Running the Simulation

```bash
python scripts/run_simulation.py --duration 60 --events-per-minute 10
```

### Generating Reports

```bash
python scripts/generate_reports.py --output-format both --include-maps
```

### Running Specific Analytics

```bash
python -m src.services.analytics_service --analyze-demand --warehouse-id all
python -m src.services.optimization_service --solve-tsp --warehouses all
```

## Docker Support

Build the Docker image:

```bash
docker build -t warehouse-management -f deployment/Dockerfile .
```

Run the container:

```bash
docker run -v $(pwd)/data:/app/data -v $(pwd)/outputs:/app/outputs warehouse-management
```

The Docker container will automatically:
1. Set up the database schema
2. Populate the database with sample data
3. Start a live event simulation in the background
4. Run all demo scripts in sequence (reporting, simulation, integration)

This provides a complete end-to-end demonstration of the warehouse management system without requiring any manual setup.

### Cleaning and Verifying Outputs

To ensure clean test runs, you can use the provided cleaning and verification scripts:

```bash
# Clean all output directories before a fresh run
python scripts/clean_outputs.py

# Run the Docker container
docker run -v $(pwd)/data:/app/data -v $(pwd)/outputs:/app/outputs warehouse-management

# Verify the generated outputs
python scripts/verify_outputs.py
```

**Note:** The current version of the analytics HTML reports may contain zeros or "Not Available" values in some cases. This is expected in the proof of concept stage and will be improved in future iterations with more comprehensive sample data.

## Database Schema

The system uses SQLite with spatial extensions and includes the following core tables:

- **products**: Product catalog with categories and attributes
- **warehouses**: Warehouse locations (sample data includes locations like Bangalore)
- **inventory**: Current stock levels across warehouses
- **purchase_events**: Historical and live purchase data
- **pincode_mapping**: Area mapping with coordinates (sample data includes regions like Bangalore)

## Demo Scenarios

1. **Stock Alert Demo**: `python scripts/run_simulation.py --scenario stock-alert`
2. **Demand Spike Simulation**: `python scripts/run_simulation.py --scenario demand-spike`
3. **Transfer Optimization**: `python scripts/run_simulation.py --scenario transfer-optimization`
4. **Manpower Planning**: `python scripts/run_simulation.py --scenario manpower-planning`
5. **High Demand Holiday**: `python -m src.examples.integration_demo`

## Reporting System

The warehouse management system includes a comprehensive reporting system with the following modules:

- **Inventory Reports**: Inventory snapshots, low stock alerts, product distribution
- **Order Reports**: Order summaries, sales reports, order status breakdowns
- **Delivery Reports**: Delivery performance, agent performance, on-time delivery rates
- **Performance Reports**:
  - Warehouse Performance: Efficiency metrics, capacity utilization
  - System Performance: System metrics, error reports, resource usage

Reports can be generated in multiple formats:
- HTML (with rich visualizations and styling)
- JSON (for data interchange)
- CSV (for spreadsheet analysis)
- PDF (for printing and distribution)

### Generated Outputs

After running the Docker container or the local workflow, the following outputs are generated in the `outputs` directory:

```
outputs/
├── charts/              # Generated chart images used in reports
├── data/                # Exported data files in various formats
├── logs/                # System and application logs
├── plots/               # Statistical plots and visualizations
└── reports/             # Generated HTML and other format reports
    ├── delivery/        # Delivery performance reports
    ├── inventory/       # Inventory status and alerts
    ├── order/           # Order summaries and sales reports
    └── performance/     # Warehouse and system performance
```

#### Key Reports and Analytics

1. **Inventory Analytics**
   - Current stock levels across warehouses
   - Low stock alerts with threshold indicators
   - Stock turnover rates and reorder suggestions

2. **Order Analytics**
   - Order volume by time period and location
   - Sales performance by product category
   - Order fulfillment rates and processing times

3. **Delivery Analytics**
   - Delivery time performance against targets
   - Delivery agent efficiency metrics
   - Geographical delivery coverage and hotspots

4. **Warehouse Performance**
   - Warehouse utilization rates
   - Processing efficiency metrics
   - Resource allocation recommendations

**Note:** In the current proof of concept stage, some reports may show placeholder values (zeros or "Not Available"). This is expected and will be improved in future iterations with more comprehensive sample data generation.
