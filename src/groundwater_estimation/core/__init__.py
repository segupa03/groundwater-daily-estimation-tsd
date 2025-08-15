"""
Core functionality for groundwater estimation.
"""

from .data_loader import (
    DataLoader, 
    SQLiteLoader, 
    ExcelLoader, 
    CSVLoader,
    create_sqlite_loader
)
from .local_regional import (
    LocalRegionalDecomposition,
    decompose_water_levels,
    estimate_daily_values
)

__all__ = [
    "DataLoader",
    "SQLiteLoader", 
    "ExcelLoader",
    "CSVLoader",
    "create_sqlite_loader",
    "LocalRegionalDecomposition",
    "decompose_water_levels",
    "estimate_daily_values"
] 