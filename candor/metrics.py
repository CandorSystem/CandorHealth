"""
CandorHealth Metrics - Failure Coverage and Robustness Measurement

These metrics quantify algorithm robustness, NOT diagnostic accuracy.
"""

import numpy as np
from typing import List, Tuple, Callable, Dict, Any
from dataclasses import dataclass


@dataclass
class RobustnessResult:
    """Results from a robustness test."""
    parameter_name: str
    parameter_values: np.ndarray
    performance_scores: np.ndarray
    failure_threshold: float
    failure_point: float  # Parameter value where failure occurs
    
    def failure_coverage_ratio(self) -> float:
        """
        Calculate FCR: proportion of parameter space where algorithm survives.
        
        FCR = (failure_point - min_value) / (max_value - min_value)
        
        Higher FCR = more robust algorithm.
        """
        min_val = self.parameter_values.min()
        max_val = self.parameter_values.max()
        
        if max_val == min_val:
            return 1.0 if self.failure_point >= max_val else 0.0
        
        fcr = (self.failure_point - min_val) / (max_val - min_val)
        return np.clip(fcr, 0.0, 1.0)


def calculate_snr(clean_signal: np.ndarray, degraded_signal: np.ndarray) -> float:
    """
    Calculate Signal-to-Noise Ratio in dB.
    
    SNR = 10 * log10(signal_power / noise_power)
    """
    noise = degraded_signal - clean_signal
    signal_power = np.mean(clean_signal ** 2)
    noise_power = np.mean(noise ** 2)
    
    if noise_power < 1e-10:
        return 100.0  # Essentially infinite SNR
    
    return 10 * np.log10(signal_power / noise_power)


def calculate_correlation(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Calculate Pearson correlation between two signals.
    
    Measures how well signal shape is preserved.
    """
    return np.corrcoef(signal1, signal2)[0, 1]


def find_failure_point(
    parameter_values: np.ndarray,
    performance_scores: np.ndarray,
    threshold: float
) -> float:
    """
    Find the parameter value where performance drops below threshold.
    
    Returns the max parameter value if no failure occurs.
    """
    failures = np.where(performance_scores < threshold)[0]
    
    if len(failures) == 0:
        return parameter_values.max()
    
    return parameter_values[failures[0]]


def generate_degradation_curve(
    crucible,
    clean_signal: np.ndarray,
    parameter_name: str,
    parameter_range: np.ndarray,
    performance_fn: Callable[[np.ndarray, np.ndarray], float],
    failure_threshold: float = 0.7
) -> RobustnessResult:
    """
    Generate a degradation curve by sweeping a parameter.
    
    Args:
        crucible: CandorCrucible instance
        clean_signal: The baseline clean signal
        parameter_name: Name of parameter to sweep (e.g., 'monk_score', 'motion_noise_level')
        parameter_range: Array of parameter values to test
        performance_fn: Function(clean, degraded) -> score (0-1)
        failure_threshold: Score below which we consider failure
        
    Returns:
        RobustnessResult with degradation curve data
    """
    scores = []
    
    for param_value in parameter_range:
        # Apply degradation with current parameter
        if parameter_name == 'monk_score':
            degraded = crucible.apply_optical_attenuation(clean_signal, param_value)
        elif parameter_name == 'motion_noise_level':
            degraded = crucible.apply_motion_artifact(clean_signal, noise_level=param_value)
        elif parameter_name == 'baseline_wander_amplitude':
            degraded = crucible.apply_motion_artifact(clean_signal, noise_level=0, wander_amplitude=param_value)
        elif parameter_name == 'mains_hum_amplitude':
            degraded = crucible.apply_mains_hum(clean_signal, amplitude=param_value)
        else:
            raise ValueError(f"Unknown parameter: {parameter_name}")
        
        # Calculate performance
        score = performance_fn(clean_signal, degraded)
        scores.append(score)
    
    scores = np.array(scores)
    failure_point = find_failure_point(parameter_range, scores, failure_threshold)
    
    return RobustnessResult(
        parameter_name=parameter_name,
        parameter_values=parameter_range,
        performance_scores=scores,
        failure_threshold=failure_threshold,
        failure_point=failure_point
    )
