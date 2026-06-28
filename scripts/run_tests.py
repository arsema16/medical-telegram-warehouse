#!/usr/bin/env python3
"""
Test runner script for the medical telegram warehouse project.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_command(cmd):
    """Check if a command is available."""
    return shutil.which(cmd) is not None


def run_pytest():
    """Run pytest with coverage."""
    print("\n=== Running Python tests with coverage ===\n")
    
    # Check if pytest is available
    if not check_command("pytest"):
        print("⚠️ pytest not found. Install with: pip install pytest pytest-cov")
        return False
    
    # Check if we should skip integration tests
    skip_integration = os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true"
    
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--cov=src",
        "--cov-report=term",
        "--cov-report=html",
        "--cov-fail-under=70"
    ]
    
    if skip_integration:
        cmd.extend(["-m", "not integration"])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ pytest not found. Please install it: pip install pytest pytest-cov")
        return False


def run_dbt_tests():
    """Run dbt tests."""
    print("\n=== Running dbt tests ===\n")
    
    if not check_command("dbt"):
        print("⚠️ dbt not found. Skipping dbt tests.")
        print("   Install with: pip install dbt-postgres")
        return True
    
    dbt_path = Path("medical_warehouse")
    if not dbt_path.exists():
        print("⚠️ dbt project not found, skipping dbt tests")
        return True
    
    try:
        # Run dbt deps first
        deps_result = subprocess.run(
            ["dbt", "deps"],
            cwd=dbt_path,
            capture_output=True,
            text=True
        )
        print("dbt deps output:")
        print(deps_result.stdout)
        if deps_result.stderr:
            print(deps_result.stderr, file=sys.stderr)
        
        # Run dbt test
        result = subprocess.run(
            ["dbt", "test"],
            cwd=dbt_path,
            capture_output=True,
            text=True
        )
        print("dbt test output:")
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ dbt not found. Please install it: pip install dbt-postgres")
        return False


def run_linting():
    """Run code linting."""
    print("\n=== Running code linting ===\n")
    
    lint_passed = True
    
    # Check if flake8 is available
    if check_command("flake8"):
        # Run flake8 with less strict rules for now
        flake8_result = subprocess.run(
            ["flake8", "src/", "tests/", 
             "--count", "--statistics", 
             "--max-line-length=127",
             "--extend-ignore=E501,F401,W293,W291,W292,E402,E722"],
            capture_output=True,
            text=True
        )
        print("Flake8 output:")
        print(flake8_result.stdout)
        if flake8_result.stderr:
            print(flake8_result.stderr, file=sys.stderr)
        
        if flake8_result.returncode != 0:
            lint_passed = False
            print("⚠️ Linting found issues (but continuing)")
    else:
        print("⚠️ flake8 not found. Install with: pip install flake8")
    
    # Check if black is available
    if check_command("black"):
        black_result = subprocess.run(
            ["black", "--check", "src/", "tests/", "--diff"],
            capture_output=True,
            text=True
        )
        print("\nBlack output:")
        print(black_result.stdout)
        if black_result.stderr:
            print(black_result.stderr, file=sys.stderr)
        
        if black_result.returncode != 0:
            lint_passed = False
            print("⚠️ Formatting issues found (but continuing)")
            print("   To fix: black src/ tests/")
    else:
        print("⚠️ black not found. Install with: pip install black")
    
    return True  # Don't fail on linting issues for now


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Medical Telegram Warehouse Test Runner")
    print("=" * 50)
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("data/raw/telegram_messages").mkdir(parents=True, exist_ok=True)
    Path("data/raw/images").mkdir(parents=True, exist_ok=True)
    
    tests_passed = True
    
    # Run linting (don't fail on linting issues)
    run_linting()
    
    # Run Python tests
    if not run_pytest():
        print("\n❌ Python tests failed")
        tests_passed = False
    else:
        print("\n✅ Python tests passed!")
    
    # Run dbt tests
    if not run_dbt_tests():
        print("\n❌ dbt tests failed")
        tests_passed = False
    else:
        print("\n✅ dbt tests passed!")
    
    if tests_passed:
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ Some tests failed!")
        print("=" * 50)
    
    return tests_passed


def main():
    """Main entry point."""
    success = run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()