"""
CandorHealth - Adversarial Validation Infrastructure for Biometric Algorithms

This package provides tools for stress-testing biometric algorithms using
physics-grounded signal degradation. It measures where algorithms fail,
not whether they're diagnostically accurate.
"""

__version__ = "0.2.0"

from .crucible import CandorCrucible, DegradationProfile
from .metrics import RobustnessResult, generate_degradation_curve, calculate_snr
from .data import PhysioNetLoader, BiosignalRecord, load_sample_ppg
from .spo2 import SpO2Simulator, SpO2Result, generate_spo2_bias_report
