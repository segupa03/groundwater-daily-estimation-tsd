"""
Performance metrics for groundwater estimation evaluation.
Based on the original errlib.py functionality.
"""

import numpy as np
from scipy import stats
from typing import Union, Tuple, Dict, Any


class PerformanceMetrics:
    """
    Class for calculating performance metrics for groundwater estimation.
    
    Includes RMSE, R², Nash-Sutcliffe Efficiency, MAPE, and Bias.
    """
    
    def __init__(self):
        """Initialize the performance metrics calculator."""
        pass
    
    def calculate_rmse(self, observed: np.ndarray, estimated: np.ndarray) -> float:
        """
        Calculate Root Mean Square Error (RMSE).
        
        Parameters:
        -----------
        observed : np.ndarray
            Observed values
        estimated : np.ndarray
            Estimated values
            
        Returns:
        --------
        float
            RMSE value
        """
        if len(observed) != len(estimated):
            raise ValueError("Observed and estimated arrays must have the same length")
        
        return np.sqrt(np.mean((observed - estimated) ** 2))
    
    def calculate_r2(self, observed: np.ndarray, estimated: np.ndarray) -> float:
        """
        Calculate coefficient of determination (R²).
        
        Parameters:
        -----------
        observed : np.ndarray
            Observed values
        estimated : np.ndarray
            Estimated values
            
        Returns:
        --------
        float
            R² value
        """
        if len(observed) != len(estimated):
            raise ValueError("Observed and estimated arrays must have the same length")
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(observed, estimated)
        return r_value ** 2
    
    def calculate_nash_sutcliffe(self, observed: np.ndarray, estimated: np.ndarray) -> float:
        """
        Calculate Nash-Sutcliffe Efficiency (NSE).
        
        Parameters:
        -----------
        observed : np.ndarray
            Observed values
        estimated : np.ndarray
            Estimated values
            
        Returns:
        --------
        float
            NSE value
        """
        if len(observed) != len(estimated):
            raise ValueError("Observed and estimated arrays must have the same length")
        
        numerator = np.sum((observed - estimated) ** 2)
        denominator = np.sum((observed - np.mean(observed)) ** 2)
        
        if denominator == 0:
            return 0.0
        
        return 1 - (numerator / denominator)
    
    def calculate_mape(self, observed: np.ndarray, estimated: np.ndarray) -> float:
        """
        Calculate Mean Absolute Percentage Error (MAPE).
        
        Parameters:
        -----------
        observed : np.ndarray
            Observed values
        estimated : np.ndarray
            Estimated values
            
        Returns:
        --------
        float
            MAPE value (percentage)
        """
        if len(observed) != len(estimated):
            raise ValueError("Observed and estimated arrays must have the same length")
        
        # Avoid division by zero
        observed_nonzero = observed[observed != 0]
        estimated_nonzero = estimated[observed != 0]
        
        if len(observed_nonzero) == 0:
            return 0.0
        
        return np.mean(np.abs((observed_nonzero - estimated_nonzero) / observed_nonzero)) * 100
    
    def calculate_bias(self, observed: np.ndarray, estimated: np.ndarray) -> float:
        """
        Calculate bias (mean error).
        
        Parameters:
        -----------
        observed : np.ndarray
            Observed values
        estimated : np.ndarray
            Estimated values
            
        Returns:
        --------
        float
            Bias value
        """
        if len(observed) != len(estimated):
            raise ValueError("Observed and estimated arrays must have the same length")
        
        return np.mean(estimated - observed)
    
    def calculate_all_metrics(self, observed: np.ndarray, estimated: np.ndarray) -> Dict[str, float]:
        """
        Calculate all performance metrics at once.
        
        Parameters:
        -----------
        observed : np.ndarray
            Observed values
        estimated : np.ndarray
            Estimated values
            
        Returns:
        --------
        Dict[str, float]
            Dictionary containing all metrics
        """
        return {
            'rmse': self.calculate_rmse(observed, estimated),
            'r2': self.calculate_r2(observed, estimated),
            'nse': self.calculate_nash_sutcliffe(observed, estimated),
            'mape': self.calculate_mape(observed, estimated),
            'bias': self.calculate_bias(observed, estimated)
        }
    
    def print_metrics(self, observed: np.ndarray, estimated: np.ndarray, 
                     title: str = "Performance Metrics") -> None:
        """
        Print all performance metrics in a formatted way.
        
        Parameters:
        -----------
        observed : np.ndarray
            Observed values
        estimated : np.ndarray
            Estimated values
        title : str, optional
            Title for the metrics report
        """
        metrics = self.calculate_all_metrics(observed, estimated)
        
        print(f"\n{title}")
        print("=" * 50)
        print(f"RMSE: {metrics['rmse']:.3f}")
        print(f"R²: {metrics['r2']:.3f}")
        print(f"Nash-Sutcliffe: {metrics['nse']:.3f}")
        print(f"MAPE: {metrics['mape']:.2f}%")
        print(f"Bias: {metrics['bias']:.3f}")
        print("=" * 50)


# Convenience functions (for backward compatibility)
def rmse(observed: np.ndarray, estimated: np.ndarray) -> float:
    """Calculate RMSE."""
    return PerformanceMetrics().calculate_rmse(observed, estimated)


def r2(observed: np.ndarray, estimated: np.ndarray) -> float:
    """Calculate R²."""
    return PerformanceMetrics().calculate_r2(observed, estimated)


def nash_sutcliffe(observed: np.ndarray, estimated: np.ndarray) -> float:
    """Calculate Nash-Sutcliffe Efficiency."""
    return PerformanceMetrics().calculate_nash_sutcliffe(observed, estimated)


def mape(observed: np.ndarray, estimated: np.ndarray) -> float:
    """Calculate MAPE."""
    return PerformanceMetrics().calculate_mape(observed, estimated)


def bias(observed: np.ndarray, estimated: np.ndarray) -> float:
    """Calculate bias."""
    return PerformanceMetrics().calculate_bias(observed, estimated)


def all_metrics(observed: np.ndarray, estimated: np.ndarray) -> Dict[str, float]:
    """Calculate all metrics."""
    return PerformanceMetrics().calculate_all_metrics(observed, estimated) 