"""
Data loader for groundwater estimation.
Supports SQLite databases, Excel files, and CSV files.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
import os
from pandas.errors import OutOfBoundsDatetime


class DataLoader:
    """
    Unified data loader for groundwater estimation.
    
    Supports multiple data sources:
    - SQLite databases
    - Excel files (.xlsx, .xls)
    - CSV files
    """
    
    def __init__(self, data_path: str, table_config: Optional[Dict[str, str]] = None):
        """
        Initialize the data loader.
        
        Parameters:
        -----------
        data_path : str
            Path to the data file (SQLite, Excel, or CSV)
        table_config : Dict[str, str], optional
            Configuration for table names (for SQLite databases)
            Default: {
                'main_table': 'WaterLevels',
                'manual_table': 'ManualMeasurements', 
                'coordinates_table': 'WellCoordinates'
            }
        """
        self.data_path = data_path
        self.data_type = self._detect_data_type()
        
        # Set default table configuration
        self.table_config = {
            'main_table': 'WaterLevels',
            'manual_table': 'ManualMeasurements',
            'coordinates_table': 'WellCoordinates'
        }
        
        # Update with user-provided configuration
        if table_config:
            self.table_config.update(table_config)
        
    def _detect_data_type(self) -> str:
        """Detect the type of data file."""
        if self.data_path.endswith('.sqlite') or self.data_path.endswith('.db'):
            return 'sqlite'
        elif self.data_path.endswith('.xlsx') or self.data_path.endswith('.xls'):
            return 'excel'
        elif self.data_path.endswith('.csv'):
            return 'csv'
        else:
            raise ValueError(f"Unsupported file type: {self.data_path}")
    
    def load_data(self) -> pd.DataFrame:
        """
        Load data from the specified source.
        
        Returns:
        --------
        pd.DataFrame
            Loaded data
        """
        if self.data_type == 'sqlite':
            return self._load_sqlite()
        elif self.data_type == 'excel':
            return self._load_excel()
        elif self.data_type == 'csv':
            return self._load_csv()
        else:
            raise ValueError(f"Unsupported data type: {self.data_type}")
    
    def _load_sqlite(self) -> pd.DataFrame:
        """Load data from SQLite database."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Database file not found: {self.data_path}")
        
        conn = sqlite3.connect(self.data_path)
        
        # Get table names
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        #print(f"Available tables: {table_names}")
        
        # Check if main table exists
        main_table = self.table_config['main_table']
        if main_table in table_names:
            query = f"""
            SELECT A, date(Jour) as 'Jour', Bassin, Puit, Zone, Ligne, Nappe 
            FROM {main_table} 
            ORDER BY Jour
            """
            df = pd.read_sql_query(query, conn)
            
            # Detect column names automatically
            column_mapping = self._detect_column_names(df)         
            
            # Retrieves the name of the column corresponding to the date (e.g., 'Jour', 'Date', etc.)
            date_col = column_mapping.get('date')
            
            # Convert Julian days to dates with robust error handling
            df[date_col] = self._convert_julian_to_date(df[date_col])
            
        else:
            print(f"Warning: Main table '{main_table}' not found.")
            print(f"Available tables: {table_names}")
            
            # If main table doesn't exist, load the first table
            first_table = table_names[0] if table_names else None
            if first_table:
                print(f"Loading first available table: {first_table}")
            df = pd.read_sql_query(f"SELECT * FROM {first_table}", conn)
            else:
                raise ValueError("No tables found in database")
        
        conn.close()
        return df
    
    def _load_excel(self) -> pd.DataFrame:
        """Load data from Excel file."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Excel file not found: {self.data_path}")
        
        # Try to read the first sheet
        try:
            df = pd.read_excel(self.data_path, sheet_name=0)
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            # Try with different engine
            df = pd.read_excel(self.data_path, sheet_name=0, engine='openpyxl')
        
        return df
    
    def _load_csv(self) -> pd.DataFrame:
        """Load data from CSV file."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"CSV file not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        # Convert date column if it exists
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        return df
    
    def _convert_julian_to_date(self, julian_series: pd.Series) -> pd.Series:
        """
        Convert Julian days to dates with robust error handling.
        
        Parameters:
        -----------
        julian_series : pd.Series
            Series containing Julian day values
            
        Returns:
        --------
        pd.Series
            Converted dates
        """
        try:
            # First, try standard Julian conversion
            return pd.to_datetime(julian_series,format="%Y-%m-%d")
        except (ValueError, OutOfBoundsDatetime) as e:
            print(f"Warning: Standard Julian conversion failed: {e}")
            print("Attempting alternative Julian formats...")
            
            # Check if values are reasonable Julian dates
            min_julian = julian_series.min()
            max_julian = julian_series.max()
            print(f"Julian range: {min_julian} to {max_julian}")
            
            # Try different Julian origins
            origins_to_try = [
                'julian',           # Standard Julian
                'unix',             # Unix timestamp
                'unix_tz',          # Unix timestamp with timezone
                'mixed',            # Mixed format
            ]
            
            for origin in origins_to_try:
                try:
                    print(f"Trying origin='{origin}'...")
                    return pd.to_datetime(julian_series, unit='D', origin=origin)
                except (ValueError, OutOfBoundsDatetime):
                    continue
            
            # If all fail, try manual conversion
            print("Attempting manual Julian conversion...")
            try:
                # Manual conversion: assume Julian day number from 1900-01-01
                base_date = pd.Timestamp('1900-01-01')
                return base_date + pd.to_timedelta(julian_series - 1, unit='D')
            except Exception as manual_error:
                print(f"Manual conversion also failed: {manual_error}")
                
                # Last resort: create sequential dates
                print("Creating sequential dates as fallback...")
                start_date = pd.Timestamp('2017-01-01')  # Default start date
                return pd.date_range(start=start_date, periods=len(julian_series), freq='D')
    
    def _detect_column_names(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect column names automatically based on data content.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Dataframe to analyze
            
        Returns:
        --------
        Dict[str, str]
            Dictionary mapping standard names to actual column names
        """
        column_mapping = {}
        
        # Detect well identifier column
        well_candidates = ['Puit', 'Well_ID', 'WellID', 'Well', 'Point']
        for candidate in well_candidates:
            if candidate in df.columns:
                column_mapping['well_id'] = candidate
                break
        
        # Detect treatment unit column
        treatment_candidates = ['Bassin', 'TreatmentUnit', 'Basin', 'Treatment', 'Unit']
        for candidate in treatment_candidates:
            if candidate in df.columns:
                column_mapping['treatment_unit'] = candidate
                break
        
        # Detect water level column
        level_candidates = ['Nappe', 'WaterLevel', 'Water_Level', 'Level', 'Depth']
        for candidate in level_candidates:
            if candidate in df.columns:
                column_mapping['water_level'] = candidate
                break
        
        # Detect date column
        date_candidates = ['Date', 'Jour', 'Day', 'Time']
        for candidate in date_candidates:
            if candidate in df.columns:
                column_mapping['date'] = candidate
                break
        
        return column_mapping
    
    def get_well_data(self, well_id: str, treatment_unit: Optional[int] = None, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get data for a specific well.
        
        Parameters:
        -----------
        well_id : str
            Well identifier
        treatment_unit : int, optional
            Treatment unit number
        start_date : str, optional
            Start date (YYYY-MM-DD format)
        end_date : str, optional
            End date (YYYY-MM-DD format)
            
        Returns:
        --------
        pd.DataFrame
            Filtered data for the specified well
        """
        df = self.load_data()
        
        # Detect column names
        column_mapping = self._detect_column_names(df)
        
        # Filter by well
        well_col = column_mapping.get('well_id')
        if well_col is None:
            raise ValueError("No well identifier column found. Expected one of: Puit, Well_ID, WellID, Well, Point")
        
        well_data = df[df[well_col] == well_id].copy()
        
        # Filter by treatment unit if specified
        if treatment_unit is not None:
            treatment_col = column_mapping.get('treatment_unit')
            if treatment_col is None:
                raise ValueError("No treatment unit column found. Expected one of: Bassin, TreatmentUnit, Basin, Treatment, Unit")
            
            well_data = well_data[well_data[treatment_col] == treatment_unit]
        
        # Filter by date range
        if start_date or end_date:
            date_col = column_mapping.get('date')
            if date_col is None:
                raise ValueError("No date column found. Expected one of: Date, Jour, Day, Time")
            
                if start_date:
                    start_dt = pd.to_datetime(start_date)
                well_data = well_data[well_data[date_col] >= start_dt]
                
                if end_date:
                    end_dt = pd.to_datetime(end_date)
                well_data = well_data[well_data[date_col] <= end_dt]

        
        # Sort by date
        date_col = column_mapping.get('date')
        if date_col:
            return well_data.sort_values(date_col)
        else:
            return well_data
    
    def get_available_wells(self) -> List[str]:
        """
        Get list of available wells.
        
        Returns:
        --------
        List[str]
            List of well identifiers
        """
        df = self.load_data()
        column_mapping = self._detect_column_names(df)
        
        well_col = column_mapping.get('well_id')
        if well_col is None:
            raise ValueError("No well identifier column found")
        
        return df[well_col].unique().tolist()
    
    def get_available_treatment_units(self) -> List[int]:
        """
        Get list of available treatment units.
        
        Returns:
        --------
        List[int]
            List of treatment unit numbers
        """
        df = self.load_data()
        column_mapping = self._detect_column_names(df)
        
        treatment_col = column_mapping.get('treatment_unit')
        if treatment_col is None:
            raise ValueError("No treatment unit column found")
        
        return df[treatment_col].unique().tolist()
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """
        Get the date range of the data.
        
        Returns:
        --------
        Tuple[datetime, datetime]
            (start_date, end_date)
        """
        df = self.load_data()
        column_mapping = self._detect_column_names(df)
        
        date_col = column_mapping.get('date')
        if date_col is None:
            raise ValueError("No date column found. Expected one of: Date, Jour, Day, Time")
        
        if date_col == 'Jour':
            # Convert Julian days to dates using robust conversion
            dates = self._convert_julian_to_date(df[date_col])
            return dates.min(), dates.max()
        else:
            # Regular date column
            return df[date_col].min(), df[date_col].max()

    def get_column_mapping(self) -> Dict[str, str]:
        """
        Get the detected column mapping for the current data.
        
        Returns:
        --------
        Dict[str, str]
            Dictionary mapping standard names to actual column names
        """
        df = self.load_data()
        return self._detect_column_names(df)
    
    def print_column_info(self) -> None:
        """
        Print information about detected columns.
        """
        df = self.load_data()
        column_mapping = self._detect_column_names(df)
        
        print("Detected column mapping:")
        for standard_name, actual_name in column_mapping.items():
            print(f"  {standard_name}: {actual_name}")
        
        print(f"\nAvailable columns: {list(df.columns)}")
        print(f"Data shape: {df.shape}")


class SQLiteLoader(DataLoader):
    """Specialized loader for SQLite databases."""
    
    def __init__(self, db_path: str, table_config: Optional[Dict[str, str]] = None):
        super().__init__(db_path, table_config)
        if self.data_type != 'sqlite':
            raise ValueError(f"Expected SQLite database, got {self.data_type}")
    
    def get_manual_measurements(self, treatment_unit: int, well: str) -> pd.DataFrame:
        """
        Get manual measurements for a specific well.
        
        Parameters:
        -----------
        treatment_unit : int
            Treatment unit number
        well : str
            Well identifier
            
        Returns:
        --------
        pd.DataFrame
            Manual measurements data
        """
        conn = sqlite3.connect(self.data_path)
        
        manual_table = self.table_config['manual_table']
        
        query = f"""
        SELECT A, Point, date(Jour+2415019) as 'Jour'
        FROM {manual_table} 
        WHERE A = ? AND Point = ?
        ORDER BY Jour
        """
        
        try:
            df = pd.read_sql_query(query, conn, params=(treatment_unit, well))
        except Exception as e:
            print(f"Error reading manual measurements from table '{manual_table}': {e}")
            print(f"Available tables: {self._get_table_names()}")
            df = pd.DataFrame()  # Return empty DataFrame if table doesn't exist
        
        conn.close()
        return df
    
    def get_well_coordinates(self) -> pd.DataFrame:
        """
        Get well coordinates.
        
        Returns:
        --------
        pd.DataFrame
            Well coordinates data
        """
        conn = sqlite3.connect(self.data_path)
        
        coords_table = self.table_config['coordinates_table']
        
        query = f"""
        SELECT Bassin, Puit, Zone, Ligne, X, Y 
        FROM {coords_table}
        """
        
        try:
        df = pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"Error reading coordinates from table '{coords_table}': {e}")
            print(f"Available tables: {self._get_table_names()}")
            df = pd.DataFrame()  # Return empty DataFrame if table doesn't exist
        
        conn.close()
        return df
    
    def _get_table_names(self) -> List[str]:
        """Get list of table names in the database."""
        conn = sqlite3.connect(self.data_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        return [table[0] for table in tables]
    
    def get_table_info(self) -> Dict[str, List[str]]:
        """
        Get information about all tables in the database.
        
        Returns:
        --------
        Dict[str, List[str]]
            Dictionary with table names as keys and column lists as values
        """
        conn = sqlite3.connect(self.data_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        table_info = {}
        for table in tables:
            table_name = table[0]
            
            # Get column information for this table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            table_info[table_name] = column_names
        
        conn.close()
        return table_info


class ExcelLoader(DataLoader):
    """Specialized loader for Excel files."""
    
    def __init__(self, excel_path: str):
        super().__init__(excel_path)
        if self.data_type != 'excel':
            raise ValueError(f"Expected Excel file, got {self.data_type}")
    
    def get_sheet_names(self) -> List[str]:
        """Get list of sheet names."""
        return pd.ExcelFile(self.data_path).sheet_names


class CSVLoader(DataLoader):
    """Specialized loader for CSV files."""
    
    def __init__(self, csv_path: str):
        super().__init__(csv_path)
        if self.data_type != 'csv':
            raise ValueError(f"Expected CSV file, got {self.data_type}") 


# Convenience function for creating loaders with custom table names
def create_sqlite_loader(db_path: str, 
                        main_table: str = 'WaterLevels',
                        manual_table: str = 'ManualMeasurements',
                        coordinates_table: str = 'WellCoordinates') -> SQLiteLoader:
    """
    Create a SQLite loader with custom table names.
    
    Parameters:
    -----------
    db_path : str
        Path to SQLite database
    main_table : str
        Name of main data table
    manual_table : str
        Name of manual measurements table
    coordinates_table : str
        Name of coordinates table
        
    Returns:
    --------
    SQLiteLoader
        Configured SQLite loader
    """
    table_config = {
        'main_table': main_table,
        'manual_table': manual_table,
        'coordinates_table': coordinates_table
    }
    
    return SQLiteLoader(db_path, table_config) 