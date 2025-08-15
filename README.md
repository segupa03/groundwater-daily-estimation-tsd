# Groundwater Daily Estimation - TSD

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

A Python package for estimating daily groundwater table values using Trend-Seasonal-Decomposition (TSD) methodology. This package provides tools for estimating daily groundwater levels from sparse observations (weekly, bi-weekly, monthly) using a reference well with daily observations.

## Overview

This methodology decomposes water table fluctuations into:
1. **Trend component** (long-term changes)
2. **Local fluctuations** (daily variations specific to each well)
3. **Regional fluctuations** (shared patterns between nearby wells)

**Regional fluctuations** are calculated as: `reference_observed - reference_trend` and are interpolated to match the target well's date range, providing daily regional patterns rather than a single average value.

## Key Features

- **Two operation modes**:
  - **Calibration Mode**: Evaluate estimation performance using known daily values
  - **Estimation Mode**: Estimate daily values when only sparse observations are available
- **Multiple data sources**: SQLite databases, Excel files (.xlsx, .xls), CSV files
- **Flexible table configuration**: Customizable table names for different database structures
- **Performance metrics**: RMSE, R², Nash-Sutcliffe Efficiency, MAPE, Bias
- **Visualization tools**: Hydrographs, observed vs. estimated plots, Taylor diagrams
- **Period filtering**: Optional filtering by specific time periods (e.g., growing season)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd groundwater-daily-estimation-tsd

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Quick Start

### Calibration Mode Example

```python
from groundwater_estimation import DataLoader, LocalRegionalDecomposition, PerformanceMetrics

# Load data
loader = DataLoader("data/groundwater_data.sqlite")
decomposition = LocalRegionalDecomposition(loader)
metrics = PerformanceMetrics()

# Get well data
target_well = "Well_001"
reference_well = "Well_002"
treatment_unit = 1
year = 2022

# Perform decomposition and estimation (mode detected automatically)
results = decomposition.estimate_daily_values(
    target_well=target_well,
    reference_well=reference_well,
    treatment_unit=treatment_unit,
    year=year
)

# Or specify mode explicitly
results = decomposition.estimate_daily_values(
    target_well=target_well,
    reference_well=reference_well,
    treatment_unit=treatment_unit,
    year=year,
    mode="calibration"  # or "estimation" or "auto"
)

# Calculate performance metrics
observed = results['observed']
estimated = results['estimated']
performance = metrics.calculate_all_metrics(observed, estimated)
print(performance)
```

### Estimation Mode Example

```python
# For estimation mode, you only need sparse observations
# The methodology will estimate daily values
results = decomposition.estimate_daily_values(
    target_well="Observation_Well",
    reference_well="Reference_Well", 
    treatment_unit=1,
    year=2022,
    mode="estimation"  # or "auto" for automatic detection
)
```

### Using Manual Measurements as Estimated Values

```python
from datetime import datetime

# Provide manual measurements as estimated values
manual_measurements = [
    (datetime(2022, 5, 20), 45.2),  # (date, water_level)
    (datetime(2022, 6, 3), 44.8),
    (datetime(2022, 6, 17), 44.5),
    (datetime(2022, 7, 1), 44.2)
]

results = decomposition.estimate_daily_values(
    target_well="Observation_Well",
    reference_well="Reference_Well",
    treatment_unit=1,
    year=2022,
    manual_measurements=manual_measurements  # These are treated as estimated values
)
```

### Automatic Mode Detection

The package can automatically detect whether you're in calibration or estimation mode:

- **Calibration Mode**: When target well has >70% daily observations
- **Estimation Mode**: When target well has sparse observations

```python
# Automatic mode detection
results = decomposition.estimate_daily_values(
    target_well="Well_001",
    reference_well="Well_002",
    treatment_unit=1,
    year=2022,
    mode="auto"  # Default behavior
)
```

## Data Organization

The package supports multiple data sources with specific organizational requirements:

### Automatic Column Detection

The package automatically detects column names from your data. Supported column name variations:

**Well Identifier:**
- `Puit`, `Well_ID`, `WellID`, `Well`, `Point`

**Treatment Unit:**
- `Bassin`, `TreatmentUnit`, `Basin`, `Treatment`, `Unit`

**Water Level:**
- `Nappe`, `WaterLevel`, `Water_Level`, `Level`, `Depth`

**Date:**
- `Date`, `Jour`, `Day`, `Time`

**Example usage:**
```python
# Check detected columns
loader = DataLoader("your_data.csv")
loader.print_column_info()

# Get column mapping
mapping = loader.get_column_mapping()
print(mapping)
# Output: {'well_id': 'Well_ID', 'treatment_unit': 'TreatmentUnit', 'water_level': 'WaterLevel', 'date': 'Date'}
```

**Note:** The decomposition engine (`LocalRegionalDecomposition`) also uses automatic column detection, so it will work with any of the supported column name variations.

### SQLite Database Structure

**Default table names** (can be customized):
- `WaterLevels`: Main data table with daily measurements
- `ManualMeasurements`: Manual measurements table
- `WellCoordinates`: Well coordinates table

**Main data table structure**:
```sql
CREATE TABLE WaterLevels (
    A INTEGER,           -- Treatment unit number
    Jour INTEGER,        -- Julian day
    Bassin INTEGER,      -- Treatment unit number (redundant with A)
    Puit TEXT,           -- Well identifier
    Zone TEXT,           -- Zone identifier
    Ligne TEXT,          -- Line identifier  
    Nappe REAL           -- Water level measurement
);
```

**Manual measurements table structure**:
```sql
CREATE TABLE ManualMeasurements (
    A INTEGER,           -- Treatment unit number
    Point TEXT,          -- Well identifier
    Jour INTEGER         -- Julian day
);
```

**Coordinates table structure**:
```sql
CREATE TABLE WellCoordinates (
    Bassin INTEGER,      -- Treatment unit number
    Puit TEXT,           -- Well identifier
    Zone TEXT,           -- Zone identifier
    Ligne TEXT,          -- Line identifier
    X REAL,              -- X coordinate
    Y REAL               -- Y coordinate
);
```

**Custom table configuration**:
```python
# Use custom table names
table_config = {
    'main_table': 'WaterLevels',
    'manual_table': 'ManualMeasurements',
    'coordinates_table': 'WellCoordinates'
}
loader = SQLiteLoader("database.sqlite", table_config)
```

### Excel Files Structure

**Option 1: Single file with multiple sheets**
```
groundwater_data.xlsx
├── Sheet1: Main data (daily measurements)
├── Sheet2: Manual measurements  
├── Sheet3: Well coordinates
└── Sheet4: Additional data
```

**Option 2: Multiple files (one per table)**
```
data/
├── daily_measurements.xlsx
├── manual_measurements.xlsx
└── well_coordinates.xlsx
```

**Required columns for main data**:
- `Well_ID`: Well identifier
- `Date`: Date (YYYY-MM-DD format)
- `TreatmentUnit`: Treatment unit number
- `WaterLevel`: Water level measurement
- `Zone` (optional): Zone identifier
- `Line` (optional): Line identifier

### CSV Files Structure

**Option 1: Single comprehensive file**
```csv
Well_ID,Date,TreatmentUnit,WaterLevel,Zone,Line,X,Y
Well_001,2022-01-01,1,45.2,Zone_A,Line_1,123.45,67.89
Well_001,2022-01-02,1,45.1,Zone_A,Line_1,123.45,67.89
...
```

**Option 2: Multiple files (one per table)**
```
data/
├── daily_measurements.csv
├── manual_measurements.csv
└── well_coordinates.csv
```

**Required columns for main data**:
- `Well_ID`: Well identifier
- `Date`: Date (YYYY-MM-DD format)
- `TreatmentUnit`: Treatment unit number
- `WaterLevel`: Water level measurement

## Performance Metrics

The package calculates the following performance metrics:

- **RMSE** (Root Mean Square Error): Measures overall accuracy
- **R²** (Coefficient of Determination): Measures goodness of fit
- **Nash-Sutcliffe Efficiency (NS)**: Measures model efficiency
- **MAPE** (Mean Absolute Percentage Error): Measures relative error
- **Bias**: Measures systematic error

## Data Structure

### Input Data Requirements

1. **Reference Well**: Must have daily observations
2. **Observation Well**: Can have sparse observations (weekly, bi-weekly, monthly)
3. **Well Coordinates**: Required for spatial analysis and nearest neighbor selection
4. **Date Range**: Consistent date format across all data sources

### Output Data Structure

The estimation process returns:
- **Daily estimated values**: Complete time series for the target well
- **Decomposition components**: Trend, local, and regional fluctuations
- **Performance metrics**: When in calibration mode
- **Visualization plots**: Hydrographs and comparison plots

## Usage Examples

### Loading Data from Different Sources

```python
# SQLite with default tables
loader = SQLiteLoader("database.sqlite")

# SQLite with custom tables
loader = create_sqlite_loader(
    db_path="database.sqlite",
    main_table="WaterLevels",
    manual_table="ManualMeasurements",
    coordinates_table="WellCoordinates"
)

# Excel file
loader = ExcelLoader("data.xlsx")

# CSV file
loader = CSVLoader("data.csv")
```

### Filtering by Time Period

```python
# Filter by growing season
results = decomposition.estimate_daily_values(
    target_well="Well_001",
    reference_well="Well_002", 
    treatment_unit=1,
    year=2022,
    start_date="2022-05-20",
    end_date="2022-10-18"
)
```

## Citation

If you use this package in your research, please cite:

```
Gutierrez Pacheco, S.; Lagacé, R.; Hugron, S.; Godbout, S.; Rochefort, L. Estimation of Daily Water Table Level with Bimonthly Measurements in Restored Ombrotrophic Peatland. Sustainability 2021, 13, 5474. https://doi.org/10.3390/su13105474 
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Note

The sample data provided in this repository is simulated and does not represent actual groundwater measurements. The original study database belongs to the [Peatland Ecology Research Group, PERG](https://www.gret-perg.ulaval.ca/en/) research group and is not included in this repository.

## Upcoming development

### **Testing and Validation**
- [ ] **Complete unit tests** for all modules
- [ ] **Multi-well test**: `test_comprehensive_multi_well_calibration_csv.py`

### **Migration and Refactoring**
- [ ] **Refactor** automatic column detection
- [ ] **Optimize** decomposition algorithms

### **New Features**
- [ ] Use `utils/plotting.py` for plotting
- [ ] **Graphical user interface** (GUI) for analysis
- [ ] **REST API** for web integration
- [ ] **Multi-language support** (French/English)
- [ ] **Advanced spatial analysis** with geostatistical interpolation

### **Documentation and Tools**
- [ ] **Interactive tutorials** (Jupyter notebooks)
- [ ] **Advanced examples** of use
- [ ] Detailed **contribution guide**

### **Infrastructure**
- [ ] **CI/CD** with GitHub Actions
- [ ] **Automated testing** on multiple Python versions
- [ ] Code quality **monitoring**



## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

# Groundwater Daily Estimation - TSD

A Python package for estimating daily groundwater table values using Trend-Seasonal-Decomposition (TSD) methodology. This package provides tools for estimating daily groundwater levels from sparse observations (weekly, bi-weekly, monthly) using a reference well with daily observations.

## Overview

This methodology decomposes water table fluctuations into:
1. **Trend component** (long-term changes)
2. **Local fluctuations** (daily variations specific to each well)
3. **Regional fluctuations** (shared patterns between nearby wells)

**Regional fluctuations** are calculated as: `reference_observed - reference_trend` and are interpolated to match the target well's date range, providing daily regional patterns rather than a single average value.

## Key Features

- **Two operation modes**:
  - **Calibration Mode**: Evaluate estimation performance using known daily values
  - **Estimation Mode**: Estimate daily values when only sparse observations are available
- **Multiple data sources**: SQLite databases, Excel files (.xlsx, .xls), CSV files
- **Flexible table configuration**: Customizable table names for different database structures
- **Performance metrics**: RMSE, R², Nash-Sutcliffe Efficiency, MAPE, Bias
- **Visualization tools**: Hydrographs, observed vs. estimated plots, Taylor diagrams
- **Period filtering**: Optional filtering by specific time periods (e.g., growing season)

## Installation

```bash
# Clone the repository
git clone https://github.com/segupa03/groundwater-daily-estimation-tsd.git
cd groundwater-daily-estimation-tsd

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Quick Start

### Calibration Mode Example

```python
from groundwater_estimation import DataLoader, LocalRegionalDecomposition, PerformanceMetrics

# Load data
loader = DataLoader("data/groundwater_data.sqlite")
decomposition = LocalRegionalDecomposition(loader)
metrics = PerformanceMetrics()

# Get well data
target_well = "Well_001"
reference_well = "Well_002"
treatment_unit = 1
year = 2022

# Perform decomposition and estimation (mode detected automatically)
results = decomposition.estimate_daily_values(
    target_well=target_well,
    reference_well=reference_well,
    treatment_unit=treatment_unit,
    year=year
)

# Or specify mode explicitly
results = decomposition.estimate_daily_values(
    target_well=target_well,
    reference_well=reference_well,
    treatment_unit=treatment_unit,
    year=year,
    mode="calibration"  # or "estimation" or "auto"
)

# Calculate performance metrics
observed = results['observed']
estimated = results['estimated']
performance = metrics.calculate_all_metrics(observed, estimated)
print(performance)
```

### Estimation Mode Example

```python
# For estimation mode, you only need sparse observations
# The methodology will estimate daily values
results = decomposition.estimate_daily_values(
    target_well="Observation_Well",
    reference_well="Reference_Well", 
    treatment_unit=1,
    year=2022,
    mode="estimation"  # or "auto" for automatic detection
)
```

### Using Manual Measurements as Estimated Values

```python
from datetime import datetime

# Provide manual measurements as estimated values
manual_measurements = [
    (datetime(2022, 5, 20), 45.2),  # (date, water_level)
    (datetime(2022, 6, 3), 44.8),
    (datetime(2022, 6, 17), 44.5),
    (datetime(2022, 7, 1), 44.2)
]

results = decomposition.estimate_daily_values(
    target_well="Observation_Well",
    reference_well="Reference_Well",
    treatment_unit=1,
    year=2022,
    manual_measurements=manual_measurements  # These are treated as estimated values
)
```

### Automatic Mode Detection

The package can automatically detect whether you're in calibration or estimation mode:

- **Calibration Mode**: When target well has >70% daily observations
- **Estimation Mode**: When target well has sparse observations

```python
# Automatic mode detection
results = decomposition.estimate_daily_values(
    target_well="Well_001",
    reference_well="Well_002",
    treatment_unit=1,
    year=2022,
    mode="auto"  # Default behavior
)
```

## Data Organization

The package supports multiple data sources with specific organizational requirements:

### Automatic Column Detection

The package automatically detects column names from your data. Supported column name variations:

**Well Identifier:**
- `Puit`, `Well_ID`, `WellID`, `Well`, `Point`

**Treatment Unit:**
- `Bassin`, `TreatmentUnit`, `Basin`, `Treatment`, `Unit`

**Water Level:**
- `Nappe`, `WaterLevel`, `Water_Level`, `Level`, `Depth`

**Date:**
- `Date`, `Jour`, `Day`, `Time`

**Example usage:**
```python
# Check detected columns
loader = DataLoader("your_data.csv")
loader.print_column_info()

# Get column mapping
mapping = loader.get_column_mapping()
print(mapping)
# Output: {'well_id': 'Well_ID', 'treatment_unit': 'TreatmentUnit', 'water_level': 'WaterLevel', 'date': 'Date'}
```

**Note:** The decomposition engine (`LocalRegionalDecomposition`) also uses automatic column detection, so it will work with any of the supported column name variations.

### SQLite Database Structure

**Default table names** (can be customized):
- `WaterLevels`: Main data table with daily measurements
- `ManualMeasurements`: Manual measurements table
- `WellCoordinates`: Well coordinates table

**Main data table structure**:
```sql
CREATE TABLE WaterLevels (
    A INTEGER,           -- Treatment unit number
    Jour INTEGER,        -- Julian day
    Bassin INTEGER,      -- Treatment unit number (redundant with A)
    Puit TEXT,           -- Well identifier
    Zone TEXT,           -- Zone identifier
    Ligne TEXT,          -- Line identifier  
    Nappe REAL           -- Water level measurement
);
```

**Manual measurements table structure**:
```sql
CREATE TABLE ManualMeasurements (
    A INTEGER,           -- Treatment unit number
    Point TEXT,          -- Well identifier
    Jour INTEGER         -- Julian day
);
```

**Coordinates table structure**:
```sql
CREATE TABLE WellCoordinates (
    Bassin INTEGER,      -- Treatment unit number
    Puit TEXT,           -- Well identifier
    Zone TEXT,           -- Zone identifier
    Ligne TEXT,          -- Line identifier
    X REAL,              -- X coordinate
    Y REAL               -- Y coordinate
);
```

**Custom table configuration**:
```python
# Use custom table names
table_config = {
    'main_table': 'WaterLevels',
    'manual_table': 'ManualMeasurements',
    'coordinates_table': 'WellCoordinates'
}
loader = SQLiteLoader("database.sqlite", table_config)
```

### Excel Files Structure

**Option 1: Single file with multiple sheets**
```
groundwater_data.xlsx
├── Sheet1: Main data (daily measurements)
├── Sheet2: Manual measurements  
├── Sheet3: Well coordinates
└── Sheet4: Additional data
```

**Option 2: Multiple files (one per table)**
```
data/
├── daily_measurements.xlsx
├── manual_measurements.xlsx
└── well_coordinates.xlsx
```

**Required columns for main data**:
- `Well_ID`: Well identifier
- `Date`: Date (YYYY-MM-DD format)
- `TreatmentUnit`: Treatment unit number
- `WaterLevel`: Water level measurement
- `Zone` (optional): Zone identifier
- `Line` (optional): Line identifier

### CSV Files Structure

**Option 1: Single comprehensive file**
```csv
Well_ID,Date,TreatmentUnit,WaterLevel,Zone,Line,X,Y
Well_001,2022-01-01,1,45.2,Zone_A,Line_1,123.45,67.89
Well_001,2022-01-02,1,45.1,Zone_A,Line_1,123.45,67.89
...
```

**Option 2: Multiple files (one per table)**
```
data/
├── daily_measurements.csv
├── manual_measurements.csv
└── well_coordinates.csv
```

**Required columns for main data**:
- `Well_ID`: Well identifier
- `Date`: Date (YYYY-MM-DD format)
- `TreatmentUnit`: Treatment unit number
- `WaterLevel`: Water level measurement

## Performance Metrics

The package calculates the following performance metrics:

- **RMSE** (Root Mean Square Error): Measures overall accuracy
- **R²** (Coefficient of Determination): Measures goodness of fit
- **Nash-Sutcliffe Efficiency (NS)**: Measures model efficiency
- **MAPE** (Mean Absolute Percentage Error): Measures relative error
- **Bias**: Measures systematic error

## Data Structure

### Input Data Requirements

1. **Reference Well**: Must have daily observations
2. **Observation Well**: Can have sparse observations (weekly, bi-weekly, monthly)
3. **Well Coordinates**: Required for spatial analysis and nearest neighbor selection
4. **Date Range**: Consistent date format across all data sources

### Output Data Structure

The estimation process returns:
- **Daily estimated values**: Complete time series for the target well
- **Decomposition components**: Trend, local, and regional fluctuations
- **Performance metrics**: When in calibration mode
- **Visualization plots**: Hydrographs and comparison plots

## Usage Examples

### Loading Data from Different Sources

```python
# SQLite with default tables
loader = SQLiteLoader("database.sqlite")

# SQLite with custom tables
loader = create_sqlite_loader(
    db_path="database.sqlite",
    main_table="WaterLevels",
    manual_table="ManualMeasurements",
    coordinates_table="WellCoordinates"
)

# Excel file
loader = ExcelLoader("data.xlsx")

# CSV file
loader = CSVLoader("data.csv")
```

### Filtering by Time Period

```python
# Filter by growing season
results = decomposition.estimate_daily_values(
    target_well="Well_001",
    reference_well="Well_002", 
    treatment_unit=1,
    year=2022,
    start_date="2022-05-20",
    end_date="2022-10-18"
)
```

## Citation

If you use this package in your research, please cite:

 Gutierrez Pacheco, S.; Lagacé, R.; Hugron, S.; Godbout, S.; Rochefort, L. **Estimation of Daily Water Table Level with Bimonthly Measurements in Restored Ombrotrophic Peatland**. _Sustainability_ 2021, 13, 5474. https://doi.org/10.3390/su13105474 


## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Note

The sample data provided in this repository is simulated and does not represent actual groundwater measurements. The original study database belongs to the [Peatland Ecology Research Group, PERG](https://www.gret-perg.ulaval.ca/en/) research group and is not included in this repository.

## Upcoming development

### **Testing and Validation**
- [ ] **Complete unit tests** for all modules
- [ ] **Multi-well test**: `test_comprehensive_multi_well_calibration_csv.py`

### **Migration and Refactoring**
- [ ] **Refactor** automatic column detection
- [ ] **Optimize** decomposition algorithms

### **New Features**
- [ ] Use `utils/plotting.py` for plotting
- [ ] **Graphical user interface** (GUI) for analysis
- [ ] **REST API** for web integration
- [ ] **Multi-language support** (French/English)
- [ ] **Advanced spatial analysis** with geostatistical interpolation

### **Documentation and Tools**
- [ ] **Interactive tutorials** (Jupyter notebooks)
- [ ] **Advanced examples** of use
- [ ] Detailed **contribution guide**

### **Infrastructure**
- [ ] **CI/CD** with GitHub Actions
- [ ] **Automated testing** on multiple Python versions
- [ ] Code quality **monitoring**



## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
