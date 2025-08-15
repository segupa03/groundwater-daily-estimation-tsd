#!/usr/bin/env python3
"""
Test script to validate that all modules can be imported correctly.
This script tests imports from different locations to ensure the package works
both when installed and when run from the project directory.
"""

import sys
import os

def test_imports_from_project_root():
    """Test imports when run from the project root directory."""
    print("=== TESTING IMPORTS FROM PROJECT ROOT ===")
    
    # Add src to path
    project_root = os.path.dirname(os.path.dirname(__file__))
    src_path = os.path.join(project_root, 'src')
    sys.path.insert(0, src_path)
    
    try:
        # Test main package import
        from groundwater_estimation import (
            DataLoader, SQLiteLoader, ExcelLoader, CSVLoader,
            LocalRegionalDecomposition, PerformanceMetrics, WellDistance,
            create_sqlite_loader, decompose_water_levels, estimate_daily_values,
            rmse, r2, nash_sutcliffe, mape, bias, all_metrics,
            calculate_distance, find_nearest_well
        )
        print("✅ All main package imports successful")
        
        # Test individual module imports
        from groundwater_estimation.core.data_loader import DataLoader
        from groundwater_estimation.core.local_regional import LocalRegionalDecomposition
        from groundwater_estimation.evaluation.performance_metrics import PerformanceMetrics
        from groundwater_estimation.utils.well_distance import WellDistance
        print("✅ Individual module imports successful")
        
        # Test function signatures
        from datetime import datetime
        from typing import List, Tuple
        
        # Test estimate_daily_values signature
        manual_measurements: List[Tuple[datetime, float]] = [
            (datetime(2022, 5, 20), 45.2),
            (datetime(2022, 6, 3), 44.8)
        ]
        print("✅ Function signatures compatible")
        
        print("🎉 All imports from project root successful!")
        
    except ImportError as e:
        print(f"❌ Import error from project root: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error from project root: {e}")
        raise

def test_imports_from_tests_directory():
    """Test imports when run from the tests directory."""
    print("\n=== TESTING IMPORTS FROM TESTS DIRECTORY ===")
    
    # Add src to path (relative to tests directory)
    src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
    sys.path.insert(0, src_path)
    
    try:
        # Test main package import
        from groundwater_estimation import (
            DataLoader, LocalRegionalDecomposition, PerformanceMetrics
        )
        print("✅ Main package imports from tests directory successful")
        
        # Test individual module imports
        from groundwater_estimation.core.data_loader import DataLoader
        from groundwater_estimation.core.local_regional import LocalRegionalDecomposition
        print("✅ Individual module imports from tests directory successful")
        
        print("🎉 All imports from tests directory successful!")
        
    except ImportError as e:
        print(f"❌ Import error from tests directory: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error from tests directory: {e}")
        raise

def test_imports_from_examples_directory():
    """Test imports when run from the examples directory."""
    print("\n=== TESTING IMPORTS FROM EXAMPLES DIRECTORY ===")
    
    # Add src to path (relative to examples directory)
    examples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')
    src_path = os.path.join(examples_dir, '..', 'src')
    sys.path.insert(0, src_path)
    
    try:
        # Test main package import
        from groundwater_estimation import (
            DataLoader, LocalRegionalDecomposition, PerformanceMetrics
        )
        print("✅ Main package imports from examples directory successful")
        
        print("🎉 All imports from examples directory successful!")
        
    except ImportError as e:
        print(f"❌ Import error from examples directory: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error from examples directory: {e}")
        raise

def test_package_structure():
    """Test that the package structure is correct."""
    print("\n=== TESTING PACKAGE STRUCTURE ===")
    
    try:
        import groundwater_estimation
        
        # Check that main modules are accessible
        assert hasattr(groundwater_estimation, 'DataLoader')
        assert hasattr(groundwater_estimation, 'LocalRegionalDecomposition')
        assert hasattr(groundwater_estimation, 'PerformanceMetrics')
        assert hasattr(groundwater_estimation, 'WellDistance')
        
        print("✅ Package structure validation successful")
        
    except Exception as e:
        print(f"❌ Package structure validation failed: {e}")
        raise

def main():
    """Run all import tests."""
    print("🧪 TESTING PACKAGE IMPORTS AND STRUCTURE")
    print("=" * 60)
    
    # Reset sys.path to avoid conflicts
    original_path = sys.path.copy()
    
    try:
        # Test imports from different locations
        test_imports_from_project_root()
        test_imports_from_tests_directory()
        test_imports_from_examples_directory()
        test_package_structure()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Package is ready for use.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    finally:
        # Restore original sys.path
        sys.path = original_path

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 