"""
CandorCrucible - Core Adversarial Validation Engine

This module implements physics-grounded signal degradation for stress-testing
biometric algorithms. It models sensor physics and environmental interference,
NOT human physiology or disease.
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class DegradationProfile:
    """Captures the parameters used to degrade a signal."""
    monk_score: Optional[float] = None
    motion_noise_level: float = 0.0
    baseline_wander_amplitude: float = 0.0
    sampling_jitter_std: float = 0.0
    burst_noise_probability: float = 0.0
    mains_hum_amplitude: float = 0.0
    
    def describe(self) -> str:
        """Human-readable description of the degradation."""
        parts = []
        if self.monk_score is not None:
            parts.append(f"Monk {self.monk_score:.1f}")
        if self.motion_noise_level > 0:
            parts.append(f"Motion noise {self.motion_noise_level:.2f}")
        if self.baseline_wander_amplitude > 0:
            parts.append(f"Baseline wander {self.baseline_wander_amplitude:.2f}")
        if self.mains_hum_amplitude > 0:
            parts.append(f"Mains hum {self.mains_hum_amplitude:.2f}")
        return " | ".join(parts) if parts else "Clean signal"


class CandorCrucible:
    """
    Adversarial Validation Engine for Biometric Signals.
    
    Applies controlled, physics-grounded degradations to biosignals
    to quantify algorithm robustness under real-world conditions.
    """
    
    def __init__(self, sample_rate: int = 100):
        """
        Initialize the Crucible.
        
        Args:
            sample_rate: Samples per second (Hz). Default 100 Hz typical for PPG.
        """
        self.sample_rate = sample_rate
    
    # =========================================================================
    # SIGNAL GENERATION (Synthetic Baselines)
    # =========================================================================
    
    def generate_synthetic_ppg(
        self, 
        duration_sec: float = 10.0, 
        heart_rate: float = 75.0,
        respiratory_rate: float = 15.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a synthetic PPG signal with realistic morphology.
        
        This is NOT a physiological model - it's a signal archetype
        for testing degradation effects.
        
        Args:
            duration_sec: Signal duration in seconds
            heart_rate: Beats per minute
            respiratory_rate: Breaths per minute (affects amplitude modulation)
            
        Returns:
            t: Time array in seconds
            signal: Normalized PPG signal (0 to 1 range)
        """
        n_samples = int(duration_sec * self.sample_rate)
        t = np.linspace(0, duration_sec, n_samples)
        
        # Cardiac frequency
        fc = heart_rate / 60.0
        
        # Build PPG morphology using harmonic components
        # Fundamental + harmonics approximate the systolic peak and dicrotic notch
        signal = (
            0.6 * np.sin(2 * np.pi * fc * t) +                    # Fundamental
            0.3 * np.sin(2 * np.pi * 2 * fc * t - np.pi/4) +      # 2nd harmonic (dicrotic)
            0.1 * np.sin(2 * np.pi * 3 * fc * t - np.pi/3)        # 3rd harmonic (shape)
        )
        
        # Add respiratory modulation (amplitude variation)
        fr = respiratory_rate / 60.0
        respiratory_envelope = 1.0 + 0.1 * np.sin(2 * np.pi * fr * t)
        signal = signal * respiratory_envelope
        
        # Normalize to 0-1 range
        signal = (signal - signal.min()) / (signal.max() - signal.min())
        
        return t, signal
    
    # =========================================================================
    # OPTICAL DEGRADATION (Beer-Lambert Physics)
    # =========================================================================
    
    def apply_optical_attenuation(
        self, 
        signal: np.ndarray, 
        monk_score: float,
        baseline_absorption: float = 0.1
    ) -> np.ndarray:
        """
        Apply Beer-Lambert optical attenuation based on skin pigmentation.
        
        Models how melanin concentration affects light transmission through tissue.
        This is sensor physics, not a demographic model.
        
        Physics: I = I_0 * exp(-μ * d)
        Where μ (absorption coefficient) correlates with melanin concentration.
        
        Args:
            signal: Input signal array
            monk_score: Monk Skin Tone scale (1-10, continuous)
            baseline_absorption: Minimum absorption even for lightest skin
            
        Returns:
            Attenuated signal
        """
        # Map Monk score to absorption coefficient
        # Monk 1 → low absorption, Monk 10 → high absorption
        # Using exponential relationship (Beer-Lambert is exponential)
        
        # Melanin absorption coefficient (relative units)
        # Calibrated so Monk 1 ≈ 90% transmission, Monk 10 ≈ 25% transmission
        mu = baseline_absorption + 0.15 * (monk_score - 1)
        
        # Apply exponential attenuation
        transmission = np.exp(-mu)
        
        # Attenuate signal amplitude (AC component)
        # DC offset shifts down as well (less light returning)
        signal_mean = signal.mean()
        signal_ac = signal - signal_mean
        
        attenuated = signal_mean * transmission + signal_ac * transmission
        
        return attenuated
    
    # =========================================================================
    # MOTION ARTIFACTS
    # =========================================================================
    
    def apply_motion_artifact(
        self,
        signal: np.ndarray,
        noise_level: float = 0.1,
        wander_amplitude: float = 0.2,
        wander_frequency: float = 0.3
    ) -> np.ndarray:
        """
        Apply motion-induced artifacts to a signal.
        
        Models:
        - High-frequency noise from sensor movement
        - Low-frequency baseline wander from body movement/breathing
        
        Args:
            signal: Input signal array
            noise_level: Standard deviation of Gaussian noise
            wander_amplitude: Amplitude of baseline wander
            wander_frequency: Frequency of baseline wander (Hz)
            
        Returns:
            Signal with motion artifacts
        """
        n_samples = len(signal)
        
        # Gaussian noise (sensor electronic noise + micro-movements)
        noise = np.random.normal(0, noise_level, n_samples)
        
        # Baseline wander (low-frequency drift from gross movement)
        t = np.arange(n_samples) / self.sample_rate
        wander = wander_amplitude * np.sin(2 * np.pi * wander_frequency * t)
        
        return signal + noise + wander
    
    def apply_burst_noise(
        self,
        signal: np.ndarray,
        probability: float = 0.01,
        burst_amplitude: float = 0.5,
        burst_duration_samples: int = 10
    ) -> np.ndarray:
        """
        Apply burst noise (sudden signal dropouts/spikes).
        
        Models poor sensor contact, sudden movements, or cable artifacts.
        
        Args:
            signal: Input signal array
            probability: Probability of burst starting at any sample
            burst_amplitude: Magnitude of burst disturbance
            burst_duration_samples: How long each burst lasts
            
        Returns:
            Signal with burst artifacts
        """
        result = signal.copy()
        n_samples = len(signal)
        
        i = 0
        while i < n_samples:
            if np.random.random() < probability:
                # Create a burst
                end = min(i + burst_duration_samples, n_samples)
                burst = np.random.uniform(-burst_amplitude, burst_amplitude, end - i)
                result[i:end] += burst
                i = end
            else:
                i += 1
        
        return result
    
    # =========================================================================
    # ENVIRONMENTAL INTERFERENCE
    # =========================================================================
    
    def apply_mains_hum(
        self,
        signal: np.ndarray,
        amplitude: float = 0.05,
        frequency: float = 60.0  # 60Hz (US) or 50Hz (EU)
    ) -> np.ndarray:
        """
        Apply power line interference (mains hum).
        
        Common in poorly shielded sensors or high-impedance contacts.
        
        Args:
            signal: Input signal array
            amplitude: Amplitude of interference
            frequency: Mains frequency (60Hz US, 50Hz EU)
            
        Returns:
            Signal with mains interference
        """
        t = np.arange(len(signal)) / self.sample_rate
        hum = amplitude * np.sin(2 * np.pi * frequency * t)
        return signal + hum
    
    def apply_sampling_jitter(
        self,
        signal: np.ndarray,
        jitter_std: float = 0.001
    ) -> np.ndarray:
        """
        Apply timing jitter (irregular sampling intervals).
        
        Models clock drift and irregular ADC timing.
        
        Args:
            signal: Input signal array  
            jitter_std: Standard deviation of timing jitter (seconds)
            
        Returns:
            Signal with interpolated jitter effects
        """
        n_samples = len(signal)
        
        # Create jittered time indices
        jitter = np.random.normal(0, jitter_std * self.sample_rate, n_samples)
        jittered_indices = np.arange(n_samples) + jitter
        jittered_indices = np.clip(jittered_indices, 0, n_samples - 1)
        
        # Interpolate to simulate effect of irregular sampling
        result = np.interp(np.arange(n_samples), jittered_indices, signal)
        
        return result
    
    # =========================================================================
    # COMPOSITE DEGRADATION PROFILES
    # =========================================================================
    
    def apply_profile(
        self,
        signal: np.ndarray,
        profile: DegradationProfile
    ) -> np.ndarray:
        """
        Apply a complete degradation profile to a signal.
        
        Args:
            signal: Input signal array
            profile: DegradationProfile specifying all degradations
            
        Returns:
            Degraded signal
        """
        result = signal.copy()
        
        if profile.monk_score is not None:
            result = self.apply_optical_attenuation(result, profile.monk_score)
        
        if profile.motion_noise_level > 0 or profile.baseline_wander_amplitude > 0:
            result = self.apply_motion_artifact(
                result,
                noise_level=profile.motion_noise_level,
                wander_amplitude=profile.baseline_wander_amplitude
            )
        
        if profile.burst_noise_probability > 0:
            result = self.apply_burst_noise(result, probability=profile.burst_noise_probability)
        
        if profile.mains_hum_amplitude > 0:
            result = self.apply_mains_hum(result, amplitude=profile.mains_hum_amplitude)
        
        if profile.sampling_jitter_std > 0:
            result = self.apply_sampling_jitter(result, jitter_std=profile.sampling_jitter_std)
        
        return result
    
    # =========================================================================
    # PRESET SCENARIOS (Regulatory-Aligned)
    # =========================================================================
    
    @staticmethod
    def scenario_lab_ideal() -> DegradationProfile:
        """Industry standard: light skin, sitting still, perfect conditions."""
        return DegradationProfile(
            monk_score=2.0,
            motion_noise_level=0.01,
            baseline_wander_amplitude=0.02
        )
    
    @staticmethod
    def scenario_real_world_moderate() -> DegradationProfile:
        """Moderate real-world: medium skin tone, light activity."""
        return DegradationProfile(
            monk_score=5.0,
            motion_noise_level=0.05,
            baseline_wander_amplitude=0.1,
            mains_hum_amplitude=0.02
        )
    
    @staticmethod
    def scenario_real_world_challenging() -> DegradationProfile:
        """Challenging: darker skin, physical activity, environmental noise."""
        return DegradationProfile(
            monk_score=8.0,
            motion_noise_level=0.12,
            baseline_wander_amplitude=0.2,
            burst_noise_probability=0.005,
            mains_hum_amplitude=0.03
        )
    
    @staticmethod
    def scenario_adversarial() -> DegradationProfile:
        """Where algorithms fail: dark skin, high motion, poor contact."""
        return DegradationProfile(
            monk_score=10.0,
            motion_noise_level=0.15,
            baseline_wander_amplitude=0.25,
            burst_noise_probability=0.01,
            mains_hum_amplitude=0.05,
            sampling_jitter_std=0.002
        )
