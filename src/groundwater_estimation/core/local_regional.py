"""
Local-regional decomposition for groundwater estimation.
Core methodology for trend-seasonal-decomposition (TSD).
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats


class LocalRegionalDecomposition:
    """
    Local-regional decomposition for groundwater level estimation.
    
    This is the core methodology that decomposes water table fluctuations into:
    1. Trend component (long-term changes)
    2. Local fluctuations (daily variations specific to each well)
    3. Regional fluctuations (shared patterns between nearby wells)
    """
    
    def __init__(self, data_loader=None):
        """
        Initialize the decomposition engine.
        
        Parameters:
        -----------
        data_loader : DataLoader, optional
            Data loader instance for accessing data
        """
        self.data_loader = data_loader
        
    def decompose_water_levels(self, well_data: pd.DataFrame, 
                              reference_data: pd.DataFrame,
                             manual_dates: Optional[List[datetime]] = None,
                             mode: str = "auto") -> Dict[str, pd.DataFrame]:
        """
        Decompose water levels into trend, local, and regional components.
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Data for the target well
        reference_data : pd.DataFrame
            Data for the reference well
        manual_dates : List[datetime], optional
            Manual measurement dates for trend calculation
        mode : str
            "auto", "calibration", or "estimation"
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            Dictionary containing trend, local, and regional components
        """
        # Determine mode automatically if not specified
        if mode == "auto":
            mode = self._detect_mode(well_data, reference_data)

        if mode == "estimation":
            date_col = self._get_date_column(well_data)
            water_level_col = self._get_water_level_column(well_data)
            manual_dates = well_data[well_data[water_level_col].notna()][date_col].values
        
        # Calculate reference well trend first
        reference_trend = self._calculate_trend_component(reference_data, manual_dates)
        
        # Calculate target well trend
        target_trend = self._calculate_trend_component(well_data, manual_dates)
        
        # Calculate regional fluctuations from reference well
        regional_fluctuations = self._calculate_regional_fluctuations(
            reference_data, reference_trend, target_trend
        )
        # TODO: check if needed. 
        # Maybe we can remove this. mode could be not needed.
        '''
        # Calculate local fluctuations (only in calibration mode)
        if mode == "calibration":
            local_fluctuations = self._calculate_local_fluctuations(well_data, target_trend)
        else:
            # In estimation mode, no local fluctuations available
            local_fluctuations = target_trend.copy()
            local_fluctuations['local_fluctuation'] = 0.0
        '''
        local_fluctuations = self._calculate_local_fluctuations(well_data, target_trend)
        
        # Combine components based on mode
        estimated_values = self._combine_components(
            well_data, target_trend, regional_fluctuations, local_fluctuations, mode
        )
        
        return {
            'trend': target_trend,
            'local': local_fluctuations,
            'regional': regional_fluctuations,
            'estimated': estimated_values,
            'mode': mode,
            'reference_trend': reference_trend
        }
    
    def _detect_mode(self, well_data: pd.DataFrame, reference_data: pd.DataFrame) -> str:
        """
        Automatically detect if we're in calibration or estimation mode.
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Target well data
        reference_data : pd.DataFrame
            Reference well data
            
        Returns:
        --------
        str
            "calibration" or "estimation"
        """
        # Check if target well has sufficient daily observations
        if 'Date' in well_data.columns:
            # Count unique dates
            unique_dates = well_data['Date'].nunique()
            total_days = (well_data['Date'].max() - well_data['Date'].min()).days + 1
            
            # If we have observations for more than 70% of days, it's calibration mode
            if unique_dates / total_days > 0.7:
                return "calibration"
            else:
                return "estimation"
        else:
            # For Julian days, check frequency
            if len(well_data) > len(reference_data) * 0.7:
                return "calibration"
            else:
                return "estimation"
    
    def _calculate_trend_component(self, well_data: pd.DataFrame, 
                                 manual_dates: Optional[List[datetime]] = None) -> pd.DataFrame:
        """
        Calculate the trend component using bi-weekly sampling.
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Well data
        manual_dates : List[datetime], optional
            Manual measurement dates (if provided, these are treated as estimated values)
            
        Returns:
        --------
        pd.DataFrame
            Trend component aligned with well_data dates
        """
        if manual_dates is None:
            # Generate bi-weekly dates
            manual_dates = self._generate_biweekly_dates(well_data)
        # Get manual measurements
        manual_measurements = self._get_manual_measurements(well_data, manual_dates)
        # Get date column
        date_col = self._get_date_column(well_data)
        
        # Interpolate to get daily trend aligned with well_data dates
        if len(manual_measurements) > 1:
            trend_values = self._interpolate_manual_measurements(well_data, manual_measurements)
        else:
            # Fallback to simple linear trend
            trend_values = self._simple_linear_trend(well_data)
        
        # Create trend DataFrame with same structure as well_data
        trend_df = pd.DataFrame({
            date_col: well_data[date_col],
            'trend': trend_values
        })

        #trend_df = well_data.copy()
        #trend_df['trend'] = trend_values
        
        return trend_df
    
    def _calculate_local_fluctuations(self, well_data: pd.DataFrame, 
                                    trend_component: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate local fluctuations (residuals from trend).
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Well data
        trend_component : pd.DataFrame
            Trend component
            
        Returns:
        --------
        pd.DataFrame
            Local fluctuations
        """
        #local_df = well_data.copy()
                
        # Get column names
        water_level_col = self._get_water_level_column(well_data)
        # Get date column
        date_col = self._get_date_column(well_data)
        
        # Calculate residuals from trend
        if water_level_col in well_data.columns and 'trend' in trend_component.columns:
            local_df = pd.DataFrame({
                date_col: well_data[date_col],
                'local_fluctuation': well_data[water_level_col] - trend_component['trend']
            })
        else:
            local_df =pd.DataFrame({
                date_col: well_data[date_col],
                'local_fluctuation': 0.0
            })
        
        return local_df
    
    def _calculate_regional_fluctuations(self, reference_data: pd.DataFrame,
                                       reference_trend: pd.DataFrame,
                                       target_trend: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate regional fluctuations from reference well.
        
        Parameters:
        -----------
        reference_data : pd.DataFrame
            Reference well data
        reference_trend : pd.DataFrame
            Reference well trend component
        target_trend : pd.DataFrame
            Target well trend component
            
        Returns:
        --------
        pd.DataFrame
            Regional fluctuations
        """
        #regional_df = target_trend.copy()
        
        # Get column names
        water_level_col = self._get_water_level_column(reference_data)
        # Get date column
        date_col = self._get_date_column(reference_data)
        
        # Calculate regional pattern from reference well fluctuations
        if len(reference_data) > 0 and water_level_col in reference_data.columns and 'trend' in reference_trend.columns:
            print(f"[local_regional.py] _calculate_regional_fluctuations: estimating regional fluctuations")
            # Regional fluctuations = reference_observed - reference_trend
            reference_fluctuations = reference_data[water_level_col].values - reference_trend['trend'].values
            
            # Interpolate regional fluctuations to target well dates
            # We need to align the reference fluctuations with target well dates
            # TODO: alert if dates are not aligned and quit calculation.
            print("length of reference fluctuations: ", len(reference_fluctuations))
            print("length of target trend: ", len(target_trend))
            if len(reference_fluctuations) == len(target_trend):
                # Same length, use directly
                regional_df = pd.DataFrame({
                    date_col: target_trend[date_col],
                    'regional_fluctuation': reference_fluctuations
                })                
            
            # This is not expected to happen      TODO !!!!!!!!!       
            else:
                print("Reference fluctuations and regional df have different lengths")
                # Different lengths, need interpolation
                # Get reference dates
                date_col = self._get_date_column(reference_data)
                if date_col == 'Jour':
                    reference_dates = self._convert_julian_to_date(reference_data[date_col])
                else:
                    reference_dates = reference_data[date_col]
                
                # Get target dates
                target_date_col = self._get_date_column(target_trend)
                # TODO: check if this is correct. Validate with a test case.
                #if target_date_col == 'Jour':
                #    target_dates = self._convert_julian_to_date(target_trend[target_date_col])
                #else:
                target_dates = target_trend[target_date_col]
                
                # Interpolate regional fluctuations to target dates
                regional_fluctuations_interpolated = np.interp(
                    pd.to_numeric(target_dates),
                    pd.to_numeric(reference_dates),
                    reference_fluctuations
                )
                
                regional_df = pd.DataFrame({
                    date_col: target_dates,
                    'regional_fluctuation': regional_fluctuations_interpolated
                })

                #regional_df['regional_fluctuation'] = regional_fluctuations_interpolated
        else:
            regional_df = pd.DataFrame({
                date_col: target_trend[date_col],
                'regional_fluctuation': 0.0
            })
        
        return regional_df
    
    def _combine_components(self, well_data: pd.DataFrame, 
                          target_trend: pd.DataFrame,
                          regional_fluctuations: pd.DataFrame,
                          local_fluctuations: pd.DataFrame,
                          mode: str) -> pd.DataFrame:
        """
        Combine all components to get final estimation.
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Well data
        target_trend : pd.DataFrame
            Trend component
        regional_fluctuations : pd.DataFrame
            Regional fluctuations
        local_fluctuations : pd.DataFrame
            Local fluctuations
        mode : str
            "calibration" or "estimation"
            
        Returns:
        --------
        pd.DataFrame
            Combined estimation
        """
        combined_df = well_data.copy()
        
        # Combine components based on mode
        if 'trend' in target_trend.columns:
            # Start with the trend component (use .values to avoid index alignment issues)
            combined_df['estimated'] = target_trend['trend'].values
            
            if mode == "calibration":
                # Mode calibration: Trend + Local fluctuations
                # Use local fluctuations from the target well itself
                if 'local_fluctuation' in local_fluctuations.columns:
                    combined_df['estimated'] += local_fluctuations['local_fluctuation'].values
                else:
                    # Fallback: use regional fluctuations if local not available
                    combined_df['estimated'] += regional_fluctuations['regional_fluctuation'].values
                    
            elif mode == "estimation":
                # Mode estimation: Trend + Regional fluctuations
                # Use regional fluctuations from the reference well
                if 'regional_fluctuation' in regional_fluctuations.columns:
                    combined_df['estimated'] += regional_fluctuations['regional_fluctuation'].values
                else:
                    # Fallback: no fluctuations if regional not available
                    pass
            else:
                # Auto mode: detect based on data density
                # If target well has many observations, use local fluctuations
                # If target well has few observations, use regional fluctuations
                if len(well_data) > len(regional_fluctuations) * 0.7:
                    # Many observations -> calibration mode
                    if 'local_fluctuation' in local_fluctuations.columns:
                        combined_df['estimated'] += local_fluctuations['local_fluctuation']
                    else:
                        combined_df['estimated'] += regional_fluctuations['regional_fluctuation']
                else:
                    # Few observations -> estimation mode
                    if 'regional_fluctuation' in regional_fluctuations.columns:
                        combined_df['estimated'] += regional_fluctuations['regional_fluctuation']
        else:
            combined_df['estimated'] = 0.0
        
        return combined_df
    
    def _align_target_with_reference_dates(self, target_data: pd.DataFrame, 
                                          reference_data: pd.DataFrame) -> pd.DataFrame:
        """
        Align target well data with reference well dates in estimation mode.
        
        This ensures that the target well has the same dates as the reference well,
        but only with values where actual measurements exist.
        
        Parameters:
        -----------
        target_data : pd.DataFrame
            Target well data (with sparse measurements)
        reference_data : pd.DataFrame
            Reference well data (with daily measurements)
            
        Returns:
        --------
        pd.DataFrame
            Target well data aligned with reference well dates
        """
        # Get column names
        date_col = self._get_date_column(reference_data)
        water_level_col = self._get_water_level_column(reference_data)
        
        # Create a DataFrame with all reference dates
        aligned_target = pd.DataFrame({
            date_col: reference_data[date_col],
            water_level_col: np.nan,  # Initialize with NaN
            'Well_ID': target_data['Well_ID'].iloc[0] if len(target_data) > 0 else 'Unknown',
            'Basin': target_data['Basin'].iloc[0] if len(target_data) > 0 else 1,
            'X': target_data['X'].iloc[0] if len(target_data) > 0 else 0,
            'Y': target_data['Y'].iloc[0] if len(target_data) > 0 else 0
        })
        
        # Add Well_type if it exists
        if 'Well_type' in target_data.columns:
            aligned_target['Well_type'] = target_data['Well_type'].iloc[0] if len(target_data) > 0 else 'Unknown'
        
        # Fill in actual measurements where they exist
        if len(target_data) > 0:
            # Convert dates to ensure compatibility
            target_dates = pd.to_datetime(target_data[date_col])
            ref_dates = pd.to_datetime(reference_data[date_col])
            
            # Find matching dates and fill values
            for idx, target_date in enumerate(target_dates):
                # Find closest reference date
                closest_idx = (ref_dates - target_date).abs().idxmin()
                aligned_target.loc[closest_idx, water_level_col] = target_data.iloc[idx][water_level_col]
        
        return aligned_target
    
    def _generate_biweekly_dates(self, well_data: pd.DataFrame) -> List[datetime]:
        """
        Generate bi-weekly sampling dates.
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Well data
            
        Returns:
        --------
        List[datetime]
            Bi-weekly dates
        """
        date_col = self._get_date_column(well_data)
        
        if date_col == 'Jour':
            # Convert Julian days to dates using robust conversion
            dates = self._convert_julian_to_date(well_data[date_col])
            start_date = dates.min()
            end_date = dates.max()
        else:
            start_date = well_data[date_col].min()
            end_date = well_data[date_col].max()
        
        # Generate bi-weekly dates
        biweekly_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            biweekly_dates.append(current_date)
            current_date += timedelta(days=14)
        
        return biweekly_dates
    
    def _get_manual_measurements(self, well_data: pd.DataFrame, 
                                manual_dates: List[datetime]) -> pd.DataFrame:
        """
        Get manual measurements for specified dates.
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Well data
        manual_dates : List[datetime]
            Manual measurement dates
            
        Returns:
        --------
        pd.DataFrame
            Manual measurements with exact dates
        """
        well_data = well_data.reset_index(drop=True).copy()
        date_col = self._get_date_column(well_data)
        water_level_col = self._get_water_level_column(well_data)
       
        # First, try to extract non-NaN values directly (for aligned data)
        non_nan_mask = well_data[water_level_col].notna()
        non_nan_mask = well_data[date_col].isin(manual_dates) & well_data[water_level_col].notna()
        if non_nan_mask.sum() > 0:
            # Extract actual measurements (non-NaN values)
            actual_measurements = well_data[non_nan_mask].copy()
            print(f"Found {len(actual_measurements)} actual measurements in aligned data")
            return actual_measurements
        
        # Fallback to original logic for non-aligned data
        if date_col == 'Date':
            # Find measurements closest to manual dates
            manual_measurements = []
            
            for manual_date in manual_dates:
                # Find closest measurement within 7 days
                time_diff = abs(well_data[date_col] - manual_date)
                closest_idx = time_diff.idxmin()
                
                if time_diff[closest_idx] <= timedelta(days=7):
                    # Use the exact manual date, not the closest measurement date
                    measurement = well_data.loc[closest_idx].copy()
                    measurement[date_col] = manual_date  # Override with exact manual date
                    manual_measurements.append(measurement)
            
            return pd.DataFrame(manual_measurements)
        else:
            # For Julian days, convert to dates and sample
            dates = self._convert_julian_to_date(well_data[date_col])
            step = len(well_data) // len(manual_dates) if manual_dates else 10
            
            manual_measurements = []
            for i, manual_date in enumerate(manual_dates):
                if i * step < len(well_data):
                    measurement = well_data.iloc[i * step].copy()
                    # Convert Julian day to exact manual date
                    measurement[date_col] = manual_date
                    manual_measurements.append(measurement)
            
            return pd.DataFrame(manual_measurements)
    
    def _interpolate_manual_measurements(self, well_data: pd.DataFrame, 
                                       manual_measurements: pd.DataFrame) -> np.ndarray:
        """
        Interpolate manual measurements to daily values.
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Well data
        manual_measurements : pd.DataFrame
            Manual measurements with exact dates
            
        Returns:
        --------
        np.ndarray
            Interpolated trend values aligned with well_data dates
        """
        if len(manual_measurements) < 2:
            return self._simple_linear_trend(well_data)
        
        # Get column names
        date_col = self._get_date_column(well_data)
        water_level_col = self._get_water_level_column(well_data)
        
        # Ensure manual measurements are sorted by date
        manual_measurements = manual_measurements.sort_values(date_col)
        
        # Get target dates (well_data dates)
        if date_col == 'Jour':
            # Convert Julian days to dates
            target_dates = self._convert_julian_to_date(well_data[date_col]).values
        else:
            target_dates = well_data[date_col].values
        
        # Get manual measurement dates and values
        manual_dates = manual_measurements[date_col].values
        manual_values = manual_measurements[water_level_col].values
        
        # Convert to numeric for interpolation
        target_dates_numeric = pd.to_numeric(target_dates)
        manual_dates_numeric = pd.to_numeric(manual_dates)
        
        # Linear interpolation
        trend_values = np.interp(
            target_dates_numeric,
            manual_dates_numeric,
            manual_values
        )
        
        return trend_values
    
    def _simple_linear_trend(self, well_data: pd.DataFrame) -> np.ndarray:
        """
        Calculate simple linear trend.
        
        Parameters:
        -----------
        well_data : pd.DataFrame
            Well data
            
        Returns:
        --------
        np.ndarray
            Linear trend values
        """
        water_level_col = self._get_water_level_column(well_data)
        
        if water_level_col not in well_data.columns:
            return np.zeros(len(well_data))
        
        # Simple linear regression
        x = np.arange(len(well_data))
        y = well_data[water_level_col].values
        
        # Remove NaN values
        mask = ~np.isnan(y)
        if np.sum(mask) < 2:
            return np.zeros(len(well_data))
        
        x_clean = x[mask]
        y_clean = y[mask]
        
        # Linear regression
        slope, intercept, _, _, _ = stats.linregress(x_clean, y_clean)
        
        # Generate trend values
        trend_values = slope * x + intercept
        
        return trend_values
    
    def estimate_daily_values(self, target_well: str, reference_well: str,
                            treatment_unit: int, year: int,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            mode: str = "auto",
                            manual_measurements: Optional[List[Tuple[datetime, float]]] = None) -> pd.DataFrame:
        """
        Estimate daily groundwater values using TSD methodology.
        
        Parameters:
        -----------
        target_well : str
            Target well identifier
        reference_well : str
            Reference well identifier
        treatment_unit : int
            Treatment unit number
        year : int
            Year for estimation
        start_date : str, optional
            Start date (YYYY-MM-DD format)
        end_date : str, optional
            End date (YYYY-MM-DD format)
        mode : str
            "auto", "calibration", or "estimation"
        manual_measurements : List[Tuple[datetime, float]], optional
            List of (date, value) tuples for manual measurements.
            These are treated as estimated values for trend calculation.
            
        Returns:
        --------
        pd.DataFrame
            Estimated daily values with components
        """
        if self.data_loader is None:
            raise ValueError("DataLoader is required for estimation")
        
        # Get well data
        target_data = self.data_loader.get_well_data(
            well_id=target_well,
            treatment_unit=treatment_unit,
            start_date=start_date,
            end_date=end_date
        )
        
        reference_data = self.data_loader.get_well_data(
            well_id=reference_well,
            treatment_unit=treatment_unit,
            start_date=start_date,
            end_date=end_date
        )
        
        # In estimation mode, ensure target well has same dates as reference well
        if mode == "estimation" or (mode == "auto" and len(target_data) < len(reference_data) * 0.7):
            target_data = self._align_target_with_reference_dates(target_data, reference_data)
        
        # Process manual measurements if provided
        manual_dates = None
        if manual_measurements is not None and mode == "estimation":
            print(f"[local_regional.py] estimate_daily_values: Manual measurements provided")
            date_col = self._get_date_column(target_data)
            # Extract dates and create a DataFrame with manual measurements
            dates, values = zip(*manual_measurements)
            manual_df = pd.DataFrame({
                date_col: dates,
                'Nappe': values
            })
            
            # Use these dates for trend calculation
            manual_dates = list(dates)
            
            # If we have manual measurements, we're likely in estimation mode
            if mode == "auto":
                mode = "estimation"
        
        elif mode == "estimation":
            print("Manual measurement from target well")
            date_col = self._get_date_column(target_data)
            manual_dates = target_data[date_col].values
        
        # Perform decomposition
        results = self.decompose_water_levels(
            target_data, reference_data, 
            manual_dates=manual_dates,
            mode=mode
        )
                
        return results['estimated']
    
    def _process_manual_measurements(self, manual_measurements: List[Tuple[datetime, float]], 
                                   target_data: pd.DataFrame) -> pd.DataFrame:
        """
        Process manual measurements as estimated values.
        
        Parameters:
        -----------
        manual_measurements : List[Tuple[datetime, float]]
            List of (date, value) tuples
        target_data : pd.DataFrame
            Target well data
            
        Returns:
        --------
        pd.DataFrame
            Processed manual measurements aligned with target data
        """
        if not manual_measurements:
            return pd.DataFrame()
        
        # Get column names
        date_col = self._get_date_column(target_data)
        water_level_col = self._get_water_level_column(target_data)
        
        # Create DataFrame from manual measurements
        dates, values = zip(*manual_measurements)
        manual_df = pd.DataFrame({
            date_col: dates,
            water_level_col: values
        })
        
        # Sort by date
        manual_df = manual_df.sort_values(date_col)
        
        return manual_df

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
            return pd.to_datetime(julian_series)
        except (ValueError, Exception) as e:
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
                except (ValueError, Exception):
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
    
    def _get_column_names(self, data: pd.DataFrame) -> Dict[str, str]:
        """
        Get column names from data_loader.
        
        Parameters:
        -----------
        data : pd.DataFrame
            Data to analyze (not used when data_loader is available)
            
        Returns:
        --------
        Dict[str, str]
            Column mapping
        """
        if self.data_loader is not None:
            return self.data_loader.get_column_mapping()
        else:
            # Fallback detection only when no data_loader is provided
            column_mapping = {}
            
            # Detect water level column
            level_candidates = ['Nappe', 'WaterLevel', 'Water_Level', 'Level', 'Depth']
            for candidate in level_candidates:
                if candidate in data.columns:
                    column_mapping['water_level'] = candidate
                    break
            
            # Detect date column
            date_candidates = ['Date', 'Jour', 'Day', 'Time']
            for candidate in date_candidates:
                if candidate in data.columns:
                    column_mapping['date'] = candidate
                    break
            
            return column_mapping
    
    def _get_water_level_column(self, data: pd.DataFrame) -> str:
        """Get water level column name."""
        if self.data_loader is not None:
            # Use data_loader's column mapping
            column_mapping = self.data_loader.get_column_mapping()
            water_level_col = column_mapping.get('water_level')
            if water_level_col is None:
                raise ValueError("No water level column found. Expected one of: Nappe, WaterLevel, Water_Level, Level, Depth")
            return water_level_col
        else:
            # Fallback detection
            column_mapping = self._get_column_names(data)
            water_level_col = column_mapping.get('water_level')
            if water_level_col is None:
                raise ValueError("No water level column found. Expected one of: Nappe, WaterLevel, Water_Level, Level, Depth")
            return water_level_col
    
    def _get_date_column(self, data: pd.DataFrame) -> str:
        """Get date column name."""
        if self.data_loader is not None:
            # Use data_loader's column mapping
            column_mapping = self.data_loader.get_column_mapping()
            date_col = column_mapping.get('date')
            if date_col is None:
                raise ValueError("No date column found. Expected one of: Date, Jour, Day, Time")
            return date_col
        else:
            # Fallback detection
            column_mapping = self._get_column_names(data)
            date_col = column_mapping.get('date')
            if date_col is None:
                raise ValueError("No date column found. Expected one of: Date, Jour, Day, Time")
            return date_col


# Convenience functions
def decompose_water_levels(well_data: pd.DataFrame, 
                          reference_data: pd.DataFrame,
                          data_loader=None,
                          mode: str = "auto",
                          manual_dates: Optional[List[datetime]] = None) -> Dict[str, pd.DataFrame]:
    """Decompose water levels into components."""
    decomposition = LocalRegionalDecomposition(data_loader)
    return decomposition.decompose_water_levels(
        well_data, reference_data, 
        manual_dates=manual_dates,
        mode=mode
    )


def estimate_daily_values(target_well: str, reference_well: str,
                         treatment_unit: int, year: int,
                        data_loader,
                        start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         mode: str = "auto",
                         manual_measurements: Optional[List[Tuple[datetime, float]]] = None) -> pd.DataFrame:
    """Estimate daily groundwater values."""
    decomposition = LocalRegionalDecomposition(data_loader)
    return decomposition.estimate_daily_values(
        target_well=target_well,
        reference_well=reference_well,
        treatment_unit=treatment_unit,
        year=year,
        start_date=start_date,
        end_date=end_date,
        mode=mode,
        manual_measurements=manual_measurements
    ) 