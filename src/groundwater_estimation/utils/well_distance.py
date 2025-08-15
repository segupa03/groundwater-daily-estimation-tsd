"""
Well distance calculator for groundwater estimation.
Based on the original Selection_voisin.py functionality.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import sqlite3


class WellDistance:
    """
    Calculate distances between wells and find nearest neighbors.
    
    Based on the original Selection_voisin.py functionality.
    """
    
    def __init__(self, data_loader=None):
        """
        Initialize the well distance calculator.
        
        Parameters:
        -----------
        data_loader : DataLoader, optional
            Data loader instance for accessing well coordinates
        """
        self.data_loader = data_loader
    
    def calculate_distance(self, well1_coords: Tuple[float, float], 
                         well2_coords: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two wells.
        
        Parameters:
        -----------
        well1_coords : Tuple[float, float]
            (X, Y) coordinates of first well
        well2_coords : Tuple[float, float]
            (X, Y) coordinates of second well
            
        Returns:
        --------
        float
            Distance in meters
        """
        x1, y1 = well1_coords
        x2, y2 = well2_coords
        
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance
    
    def get_well_coordinates(self, treatment_unit: int, well: str) -> Tuple[float, float]:
        """
        Get coordinates for a specific well.
        
        Parameters:
        -----------
        treatment_unit : int
            Treatment unit number
        well : str
            Well identifier
            
        Returns:
        --------
        Tuple[float, float]
            (X, Y) coordinates
        """
        if self.data_loader is None:
            raise ValueError("DataLoader is required to get well coordinates")
        
        # Get coordinates from the data loader
        coords_df = self.data_loader.get_well_coordinates()
        
        # Filter by treatment unit and well
        well_coords = coords_df[
            (coords_df['Bassin'] == treatment_unit) & 
            (coords_df['Puit'] == well)
        ]
        
        if len(well_coords) == 0:
            raise ValueError(f"No coordinates found for well {well} in treatment unit {treatment_unit}")
        
        return (well_coords.iloc[0]['X'], well_coords.iloc[0]['Y'])
    
    def find_nearest_well(self, target_treatment_unit: int, target_well: str, 
                         candidate_wells: List[Tuple[int, str]], 
                         max_distance: Optional[float] = None) -> Tuple[Tuple[int, str], float]:
        """
        Find the nearest well from a list of candidates.
        
        Parameters:
        -----------
        target_treatment_unit : int
            Treatment unit of target well
        target_well : str
            Target well identifier
        candidate_wells : List[Tuple[int, str]]
            List of (treatment_unit, well) candidates
        max_distance : float, optional
            Maximum distance to consider
            
        Returns:
        --------
        Tuple[Tuple[int, str], float]
            (nearest_well, distance)
        """
        target_coords = self.get_well_coordinates(target_treatment_unit, target_well)
        
        min_distance = float('inf')
        nearest_well = None
        
        for treatment_unit, well in candidate_wells:
            if treatment_unit == target_treatment_unit and well == target_well:
                continue  # Skip self
                
            try:
                candidate_coords = self.get_well_coordinates(treatment_unit, well)
                distance = self.calculate_distance(target_coords, candidate_coords)
                
                if distance < min_distance and (max_distance is None or distance <= max_distance):
                    min_distance = distance
                    nearest_well = (treatment_unit, well)
                    
            except ValueError:
                # Skip wells without coordinates
                continue
        
        if nearest_well is None:
            raise ValueError(f"No suitable nearest well found for {target_well}")
        
        return nearest_well, min_distance
    
    def find_nearest_wells(self, target_treatment_unit: int, target_well: str, 
                          candidate_wells: List[Tuple[int, str]], 
                          n_neighbors: int = 3,
                          max_distance: Optional[float] = None) -> List[Tuple[Tuple[int, str], float]]:
        """
        Find the n nearest wells from a list of candidates.
        
        Parameters:
        -----------
        target_treatment_unit : int
            Treatment unit of target well
        target_well : str
            Target well identifier
        candidate_wells : List[Tuple[int, str]]
            List of (treatment_unit, well) candidates
        n_neighbors : int
            Number of nearest neighbors to find
        max_distance : float, optional
            Maximum distance to consider
            
        Returns:
        --------
        List[Tuple[Tuple[int, str], float]]
            List of (well, distance) tuples, sorted by distance
        """
        target_coords = self.get_well_coordinates(target_treatment_unit, target_well)
        
        distances = []
        
        for treatment_unit, well in candidate_wells:
            if treatment_unit == target_treatment_unit and well == target_well:
                continue  # Skip self
                
            try:
                candidate_coords = self.get_well_coordinates(treatment_unit, well)
                distance = self.calculate_distance(target_coords, candidate_coords)
                
                if max_distance is None or distance <= max_distance:
                    distances.append(((treatment_unit, well), distance))
                    
            except ValueError:
                # Skip wells without coordinates
                continue
        
        # Sort by distance and return top n
        distances.sort(key=lambda x: x[1])
        return distances[:n_neighbors]
    
    def get_wells_within_radius(self, target_treatment_unit: int, target_well: str, 
                               candidate_wells: List[Tuple[int, str]], 
                               radius: float) -> List[Tuple[Tuple[int, str], float]]:
        """
        Find all wells within a specified radius.
        
        Parameters:
        -----------
        target_treatment_unit : int
            Treatment unit of target well
        target_well : str
            Target well identifier
        candidate_wells : List[Tuple[int, str]]
            List of (treatment_unit, well) candidates
        radius : float
            Search radius in meters
            
        Returns:
        --------
        List[Tuple[Tuple[int, str], float]]
            List of (well, distance) tuples within radius
        """
        target_coords = self.get_well_coordinates(target_treatment_unit, target_well)
        
        wells_in_radius = []
        
        for treatment_unit, well in candidate_wells:
            if treatment_unit == target_treatment_unit and well == target_well:
                continue  # Skip self
                
            try:
                candidate_coords = self.get_well_coordinates(treatment_unit, well)
                distance = self.calculate_distance(target_coords, candidate_coords)
                
                if distance <= radius:
                    wells_in_radius.append(((treatment_unit, well), distance))
                    
            except ValueError:
                # Skip wells without coordinates
                continue
        
        # Sort by distance
        wells_in_radius.sort(key=lambda x: x[1])
        return wells_in_radius
    
    def create_distance_matrix(self, wells: List[Tuple[int, str]]) -> pd.DataFrame:
        """
        Create a distance matrix between all wells.
        
        Parameters:
        -----------
        wells : List[Tuple[int, str]]
            List of (treatment_unit, well) tuples
            
        Returns:
        --------
        pd.DataFrame
            Distance matrix with well identifiers as index and columns
        """
        n_wells = len(wells)
        distance_matrix = np.zeros((n_wells, n_wells))
        
        # Calculate distances
        for i, (treatment_unit1, well1) in enumerate(wells):
            try:
                coords1 = self.get_well_coordinates(treatment_unit1, well1)
                
                for j, (treatment_unit2, well2) in enumerate(wells):
                    if i == j:
                        distance_matrix[i, j] = 0.0
                    else:
                        try:
                            coords2 = self.get_well_coordinates(treatment_unit2, well2)
                            distance_matrix[i, j] = self.calculate_distance(coords1, coords2)
                        except ValueError:
                            distance_matrix[i, j] = np.nan
                            
            except ValueError:
                # If coordinates not found, set all distances to NaN
                distance_matrix[i, :] = np.nan
        
        # Create DataFrame
        well_names = [f"{treatment_unit}-{well}" for treatment_unit, well in wells]
        df = pd.DataFrame(distance_matrix, index=well_names, columns=well_names)
        
        return df


# Convenience functions (for backward compatibility)
def calculate_distance(well1_coords: Tuple[float, float], 
                     well2_coords: Tuple[float, float]) -> float:
    """Calculate distance between two wells."""
    return WellDistance().calculate_distance(well1_coords, well2_coords)


def find_nearest_well(target_treatment_unit: int, target_well: str, 
                     candidate_wells: List[Tuple[int, str]], 
                     data_loader) -> Tuple[Tuple[int, str], float]:
    """Find nearest well."""
    calculator = WellDistance(data_loader)
    return calculator.find_nearest_well(target_treatment_unit, target_well, candidate_wells) 