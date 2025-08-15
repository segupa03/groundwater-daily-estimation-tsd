"""
Groundwater Daily Estimation - TSD Package

A Python package for estimating daily groundwater table values using 
Trend-Seasonal-Decomposition (TSD) methodology.
"""

__version__ = "0.1.0"
__author__ = "Groundwater Research Team"

# Core modules
from .core.data_loader import (
    DataLoader, 
    SQLiteLoader, 
    ExcelLoader, 
    CSVLoader,
    create_sqlite_loader
)

from .core.local_regional import (
    LocalRegionalDecomposition,
    decompose_water_levels,
    estimate_daily_values
)

# Evaluation modules
from .evaluation.performance_metrics import (
    PerformanceMetrics,
    rmse,
    r2,
    nash_sutcliffe,
    mape,
    bias,
    all_metrics
)

# Utils modules
from .utils.well_distance import (
    WellDistance,
    calculate_distance,
    find_nearest_well
)

# Convenience imports for common use cases
__all__ = [
    # Core classes
    'DataLoader',
    'SQLiteLoader', 
    'ExcelLoader',
    'CSVLoader',
    'LocalRegionalDecomposition',
    'PerformanceMetrics',
    'WellDistance',
    
    # Core functions
    'create_sqlite_loader',
    'decompose_water_levels',
    'estimate_daily_values',
    
    # Performance metrics
    'rmse',
    'r2', 
    'nash_sutcliffe',
    'mape',
    'bias',
    'all_metrics',
    
    # Utility functions
    'calculate_distance',
    'find_nearest_well'
] 