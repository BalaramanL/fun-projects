#!/bin/bash
# Entrypoint script for the warehouse management system Docker container
# This script runs the database setup and population scripts first,
# then launches the demo scenarios in sequence

set -e  # Exit on error

echo "Starting warehouse management system setup..."

# Ensure data directory exists
mkdir -p /app/data

# Run database setup and population
echo "Setting up and populating the database..."
python /app/scripts/run_all_setup.py

# Wait a moment to ensure database is ready
sleep 2

# Start the live event simulation in the background
echo "Starting live event simulation in the background..."
python /app/scripts/simulate_live_events.py --events-per-minute 5 &
SIMULATION_PID=$!

# Wait a moment for simulation to start
sleep 2

# Run the demo scenarios
echo "Running reporting demo..."
python /app/src/examples/reporting_demo.py

echo "Running simulation demo..."
python /app/src/examples/simulation_demo.py

echo "Running integration demo..."
python /app/src/examples/integration_demo.py

echo "Running complete workflow demo..."
python /app/src/examples/run_complete_workflow.py

# Keep the container running with the simulation
echo "All demos completed. Live simulation is still running."
echo "Press Ctrl+C to stop the container."

# Wait for the simulation process
wait $SIMULATION_PID
