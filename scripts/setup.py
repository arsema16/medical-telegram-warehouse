#!/usr/bin/env python3
"""
Setup script for the medical telegram warehouse project.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and print output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def setup_environment():
    """Setup the Python environment."""
    print("\n=== Setting up Python environment ===")
    
    # Create virtual environment
    if not Path(".venv").exists():
        run_command("python -m venv .venv")
    
    # Install requirements
    pip_cmd = ".venv/bin/pip" if os.name != "nt" else ".venv\\Scripts\\pip"
    run_command(f"{pip_cmd} install --upgrade pip")
    run_command(f"{pip_cmd} install -r requirements.txt")

def setup_dbt():
    """Setup dbt project."""
    print("\n=== Setting up dbt project ===")
    
    # Install dbt packages
    os.chdir("medical_warehouse")
    run_command("dbt deps")
    os.chdir("..")

def setup_database():
    """Setup database using docker-compose."""
    print("\n=== Setting up database with docker-compose ===")
    
    # Start PostgreSQL
    run_command("docker-compose up -d postgres")
    
    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    run_command("sleep 5")

def run_tests():
    """Run tests."""
    print("\n=== Running tests ===")
    
    # Run Python tests
    run_command("pytest tests/ -v --cov=src --cov-report=term")
    
    # Run dbt tests
    os.chdir("medical_warehouse")
    run_command("dbt test")
    os.chdir("..")

def main():
    """Main setup function."""
    print("=" * 50)
    print("Medical Telegram Warehouse Setup")
    print("=" * 50)
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("\n⚠️  .env file not found. Please create one with your credentials.")
        print("   Copy .env.example to .env and fill in your values.")
        return
    
    setup_environment()
    setup_database()
    setup_dbt()
    
    # Run scraped data load
    print("\n=== Loading scraped data ===")
    run_command("python src/data_loader.py")
    
    # Run dbt transformations
    print("\n=== Running dbt transformations ===")
    os.chdir("medical_warehouse")
    run_command("dbt run")
    run_command("dbt test")
    os.chdir("..")
    
    # Generate dbt documentation
    print("\n=== Generating dbt documentation ===")
    os.chdir("medical_warehouse")
    run_command("dbt docs generate")
    os.chdir("..")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Run scraper: python src/scraper.py")
    print("2. View dbt docs: cd medical_warehouse && dbt docs serve")
    print("3. Start API: uvicorn api.main:app --reload")

if __name__ == "__main__":
    main()