#!/usr/bin/env python3
"""
Test runner script for the project research hack integration tests.
"""

import sys
import subprocess
from pathlib import Path


def run_tests(test_type="all", verbose=False):
    """Run tests with specified options."""
    
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    # Add test selection based on type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "ado":
        cmd.extend(["-m", "ado"])
    elif test_type == "azure":
        cmd.extend(["-m", "azure"])
    elif test_type == "mcp":
        cmd.extend(["-m", "mcp"])
    elif test_type == "research":
        cmd.extend(["-m", "research"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    elif test_type == "all":
        pass  # Run all tests
    else:
        print(f"Unknown test type: {test_type}")
        return False
    
    cmd.append("tests/")
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with return code: {e.returncode}")
        return False


def main():
    """Main test runner."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Run project research hack tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "ado", "azure", "mcp", "research", "fast", "slow"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--list-tests",
        action="store_true", 
        help="List available tests without running them"
    )
    
    args = parser.parse_args()
    
    if args.list_tests:
        print("Available test commands:")
        print("  python run_tests.py --type unit          # Unit tests only")
        print("  python run_tests.py --type integration   # Integration tests only") 
        print("  python run_tests.py --type ado           # ADO-related tests")
        print("  python run_tests.py --type azure         # Azure AI tests")
        print("  python run_tests.py --type mcp           # MCP server tests")
        print("  python run_tests.py --type research      # Research pipeline tests")
        print("  python run_tests.py --type fast          # Fast tests (exclude slow)")
        print("  python run_tests.py --type slow          # Slow tests only")
        print("  python run_tests.py --type all           # All tests")
        print()
        print("Example usage:")
        print("  python run_tests.py --type fast -v       # Fast tests with verbose output")
        print("  python run_tests.py --type unit          # Quick unit tests")
        print("  python run_tests.py --type integration   # Full integration tests")
        return
    
    print(f"🧪 Running {args.type} tests...")
    print()
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed. Install with: pip install pytest")
        sys.exit(1)
    
    # Run tests
    success = run_tests(args.type, args.verbose)
    
    if success:
        print("\n✅ Tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()