#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to create sample data for the groundwater estimation package.
This generates simulated data based on the structure of the original database.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_realistic_water_levels(well, basin, days, noise_level=0.30):
    """
    Generate realistic water levels with adjustable noise.
    
    Parameters:
    -----------
    well : str
        Well identifier
    basin : int
        Basin number
    days : int
        Number of days
    noise_level : float
        Noise intensity multiplier (0.30 = normal for water level, 1.0 = high noise, 0.15 = low noise)
        
    Returns:
    --------
    np.ndarray
        Water levels
    """
    # Base level with basin and well variations
    base_level = -20 + basin * 5
    well_offset = hash(well) % 10 - 5
    base_level += well_offset
    
    # Trend with variation
    trend = np.linspace(0, -5 + np.random.normal(0, 2), days)
    
    # Seasonal variation with phase shift per well
    phase_shift = (hash(well) % 30) / 365
    seasonal = 3 * np.sin(2 * np.pi * (np.arange(days) / 365 + phase_shift))
    
    # Multiple noise sources scaled by noise_level
    daily_noise = noise_level * np.random.normal(0, 2, days)
    weekly_pattern = noise_level * 1.5 * np.sin(2 * np.pi * np.arange(days) / 7)
    monthly_pattern = noise_level * 2 * np.sin(2 * np.pi * np.arange(days) / 30)
    
    # Random events
    events = np.random.choice([0, 1], size=days, p=[0.95, 0.05])
    event_effects = noise_level * events * np.random.normal(0, 3, days)
    
    # Measurement errors
    measurement_error = noise_level * np.random.normal(0, 0.5, days)
    
    # Combine all components
    water_levels = (base_level + trend + seasonal + 
                   daily_noise + weekly_pattern + monthly_pattern + 
                   event_effects + measurement_error)
    
    # Ensure realistic bounds
    water_levels = np.clip(water_levels, -50, 10)
    
    return water_levels

def create_sample_database(noise_level=0.30):
    """Create a sample SQLite database with simulated data."""
    
    # Create database
    db_path = "data/sample_data/sample_database.sqlite"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables based on original structure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS WaterLevels (
            A INTEGER,
            Jour INTEGER,
            Bassin INTEGER,
            Puit CHAR,
            Zone INTEGER,
            Ligne CHAR,
            Nappe DOUBLE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ManualMeasurements (
            A INTEGER,
            Point INTEGER,
            Jour INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS WellCoordinates (
            Bassin DECIMAL,
            Puit CHAR,
            Zone INTEGER,
            Ligne CHAR,
            X DOUBLE,
            Y DOUBLE
        )
    ''')
    
    # Generate sample data
    print("Generating sample data...")
    
    # Wells configuration
    wells = {
        1: ['A', 'B', 'C', 'D', 'E'],  # Basin 1
        2: ['F', 'G', 'H', 'I', 'J'],  # Basin 2
        3: ['K', 'L', 'M', 'N', 'O']   # Basin 3
    }
    
    # Coordinates for wells (simulated)
    coordinates = {}
    for basin in wells:
        for i, well in enumerate(wells[basin]):
            coordinates[(basin, well)] = (100 + basin * 50 + i * 10, 200 + basin * 30 + i * 8)
    
    # Generate daily data for 2017 growing season (May 20 - Oct 18)
    start_date = datetime(2017, 5, 20)
    end_date = datetime(2017, 10, 18)
    date_range = pd.date_range(start_date, end_date, freq='D')    
    
    sample_data_ll = []
    sample_data_m = []
    sample_coordinates = []
    
    # Generate data for each well
    for basin in wells:
        for well in wells[basin]:
            x, y = coordinates[(basin, well)]
            
            # Add coordinates
            sample_coordinates.append([basin, well, 1, 'A', x, y])
            
            # Generate daily water levels with realistic patterns using the new function
            water_levels = generate_realistic_water_levels(well, basin, len(date_range), noise_level=noise_level)
            
            # Add daily data (LL - continuous monitoring)
            for date in date_range:
                sample_data_ll.append([
                    2017, date, basin, well, 1, 'A', water_levels[i]
                ])
            
            # Add manual measurements (M - bi-weekly)
            manual_dates = date_range[::14]  # Every 14 days
            for i, date in enumerate(manual_dates):
                sample_data_m.append([
                    2017, i + 1, date
                ])
    
    # Insert data
    cursor.executemany('''
        INSERT INTO WaterLevels (A, Jour, Bassin, Puit, Zone, Ligne, Nappe)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', sample_data_ll)
    
    cursor.executemany('''
        INSERT INTO ManualMeasurements (A, Point, Jour)
        VALUES (?, ?, ?)
    ''', sample_data_m)
    
    cursor.executemany('''
        INSERT INTO WellCoordinates (Bassin, Puit, Zone, Ligne, X, Y)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_coordinates)
    
    conn.commit()
    conn.close()
    
    print(f"Sample database created: {db_path}")
    print(f"  - {len(sample_data_ll)} daily records")
    print(f"  - {len(sample_data_m)} manual measurement records")
    print(f"  - {len(sample_coordinates)} well coordinates")

def create_sample_excel(noise_level=0.30):
    """Create sample Excel file with simulated data."""
    
    # Generate sample data
    wells = ['well_A', 'well_B', 'well_C', 'well_D', 'well_E']
    basins = [1, 1, 2, 2, 3]
    coordinates = [(100, 200), (110, 210), (150, 230), (160, 240), (200, 260)]
    
    # Date range
    start_date = datetime(2017, 5, 20)
    end_date = datetime(2017, 10, 18)
    date_range = pd.date_range(start_date, end_date, freq='D')
    
    # Create sample data
    sample_data = []
    
    for i, well in enumerate(wells):
        basin = basins[i]
        x, y = coordinates[i]
        
        # Generate water levels using the new realistic function
        water_levels = generate_realistic_water_levels(well, basin, len(date_range), noise_level=noise_level)
        
        for j, date in enumerate(date_range):
            sample_data.append({
                'Date': date,
                'Well_ID': well,
                'Water_Level': water_levels[j],
                'Basin': basin,
                'X': x,
                'Y': y
            })
    
    # Create DataFrame and save
    df = pd.DataFrame(sample_data)
    
    excel_path = "data/sample_data/sample_data.xlsx"
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Water_Levels', index=False)
        
        # Create additional sheet with well information
        well_info = pd.DataFrame({
            'Well_ID': wells,
            'Basin': basins,
            'X': [coord[0] for coord in coordinates],
            'Y': [coord[1] for coord in coordinates],
            'Type': ['Reference', 'Target', 'Target', 'Target', 'Target']
        })
        well_info.to_excel(writer, sheet_name='Well_Info', index=False)
    
    print(f"Sample Excel file created: {excel_path}")
    print(f"  - {len(sample_data)} records")
    print(f"  - {len(wells)} wells")

def create_sample_csv(noise_level=0.30):
    """Create sample CSV file with simulated data."""
    
    # Generate sample data
    wells = ['well_A', 'well_B', 'well_C', 'well_D', 'well_E']
    basins = [1, 1, 2, 2, 3]
    coordinates = [(100, 200), (110, 210), (150, 230), (160, 240), (200, 260)]
    
    # Date range
    start_date = datetime(2017, 5, 20)
    end_date = datetime(2017, 10, 18)
    date_range = pd.date_range(start_date, end_date, freq='D')
    
    # Create sample data
    sample_data = []
    
    for i, well in enumerate(wells):
        basin = basins[i]
        x, y = coordinates[i]
        
        # Generate water levels using the new realistic function
        water_levels = generate_realistic_water_levels(well, basin, len(date_range), noise_level=noise_level)
        
        for j, date in enumerate(date_range):
            sample_data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Well_ID': well,
                'Water_Level': water_levels[j],
                'Basin': basin,
                'X': x,
                'Y': y
            })
    
    # Create DataFrame and save
    df = pd.DataFrame(sample_data)
    
    csv_path = "data/sample_data/sample_data.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    df.to_csv(csv_path, index=False)
    
    print(f"Sample CSV file created: {csv_path}")
    print(f"  - {len(sample_data)} records")
    print(f"  - {len(wells)} wells")

def main():
    """Create all sample data files."""
    print("Creating sample data for groundwater estimation package...")
    print("=" * 60)
    
    # You can adjust the noise level here:
    # noise_level = 0.30  # Low noise (default)
    # noise_level = 0.50 # Normal noise 
    # noise_level = 1.0  # High noise (very noisy data)
    noise_level = 0.30
    
    print(f"Using noise level: {noise_level}")
    
    create_sample_excel(noise_level=noise_level)
    print()
    create_sample_csv(noise_level=noise_level)
    print()
    
    print("Sample data creation completed!")
    print("\nFiles created:")
    print("  - data/sample_data/sample_data.xlsx")
    print("  - data/sample_data/sample_data.csv")
    print("\nNote: These are simulated data files for testing purposes.")
    print("They do not correspond to actual study data.")

if __name__ == "__main__":
    main() 