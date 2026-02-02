"""
CandorHealth SpO2 Simulation Module

Models pulse oximetry physics including:
- Red (660nm) and Infrared (940nm) light absorption
- Hemoglobin oxygen saturation effects
- Melanin absorption bias across skin tones

This is SENSOR PHYSICS modeling, not physiological simulation.
"""

import numpy as np
from typing import Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class SpO2Result:
    """Results from SpO2 estimation."""
    true_spo2: float          # Actual SpO2 (ground truth)
    estimated_spo2: float     # What the algorithm reports
    bias: float               # estimated - true (positive = overestimation)
    r_ratio: float            # Red/IR ratio used for estimation
    signal_quality_red: float # Correlation of red signal
    signal_quality_ir: float  # Correlation of IR signal
    
    @property
    def clinically_significant(self) -> bool:
        """FDA considers >3% SpO2 bias clinically significant."""
        return abs(self.bias) > 3.0
    
    @property
    def dangerous_overestimate(self) -> bool:
        """Overestimation can delay treatment for hypoxia."""
        return self.bias > 2.0 and self.estimated_spo2 >= 94.0


class SpO2Simulator:
    """
    Simulates pulse oximetry signal generation and SpO2 estimation.
    
    Physics Background:
    - SpO2 is estimated from the ratio of pulsatile (AC) to static (DC) 
      components at red (660nm) and infrared (940nm) wavelengths
    - R = (AC_red/DC_red) / (AC_ir/DC_ir)
    - SpO2 ≈ 110 - 25*R (simplified linear calibration)
    
    Melanin Effect:
    - Melanin absorbs both wavelengths but affects red more than IR
    - This shifts the R ratio, causing SpO2 overestimation in darker skin
    - This is the core bias that FDA guidance addresses
    """
    
    def __init__(self, sample_rate: int = 125):
        self.sample_rate = sample_rate
        
        # Absorption coefficients (relative units, calibrated for simulation)
        # Based on Beer-Lambert: I = I_0 * exp(-μ * d)
        
        # Melanin absorption (higher for red than IR)
        self.melanin_absorption_red = 0.12    # at 660nm
        self.melanin_absorption_ir = 0.04     # at 940nm
        
        # Hemoglobin absorption coefficients
        # HbO2 (oxygenated): absorbs more IR
        # Hb (deoxygenated): absorbs more red
        self.hbo2_absorption_red = 0.1
        self.hbo2_absorption_ir = 0.25
        self.hb_absorption_red = 0.4
        self.hb_absorption_ir = 0.15
    
    def generate_ppg_dual_wavelength(
        self,
        duration_sec: float = 10.0,
        heart_rate: float = 70.0,
        true_spo2: float = 97.0,
        monk_score: float = 2.0,
        perfusion_index: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate red and IR PPG signals for a given SpO2 and skin tone.
        
        Args:
            duration_sec: Signal duration
            heart_rate: Heart rate in BPM
            true_spo2: Actual oxygen saturation (%)
            monk_score: Monk Skin Tone (1-10)
            perfusion_index: Blood perfusion (1.0 = normal, lower = weaker pulse)
            
        Returns:
            t: Time array
            ppg_red: Red wavelength PPG signal
            ppg_ir: Infrared wavelength PPG signal
        """
        n_samples = int(duration_sec * self.sample_rate)
        t = np.linspace(0, duration_sec, n_samples)
        fc = heart_rate / 60.0
        
        # Base PPG morphology (same shape for both wavelengths)
        ppg_base = (
            0.5 * np.sin(2 * np.pi * fc * t) +
            0.2 * np.sin(2 * np.pi * 2 * fc * t - np.pi/4) +
            0.1 * np.sin(2 * np.pi * 3 * fc * t - np.pi/3)
        )
        
        # Add respiratory modulation
        fr = 15 / 60.0
        ppg_base = ppg_base * (1.0 + 0.05 * np.sin(2 * np.pi * fr * t))
        
        # Calculate fractional hemoglobin concentrations
        spo2_fraction = true_spo2 / 100.0
        hbo2_fraction = spo2_fraction
        hb_fraction = 1.0 - spo2_fraction
        
        # Calculate melanin absorption based on Monk score
        # Monk 1 = minimal melanin, Monk 10 = high melanin
        melanin_factor = (monk_score - 1) / 9.0  # 0 to 1
        
        melanin_abs_red = self.melanin_absorption_red * melanin_factor
        melanin_abs_ir = self.melanin_absorption_ir * melanin_factor
        
        # Calculate total absorption for each wavelength
        # Red: high Hb absorption + melanin
        # IR: high HbO2 absorption + less melanin
        
        total_abs_red = (
            hbo2_fraction * self.hbo2_absorption_red +
            hb_fraction * self.hb_absorption_red +
            melanin_abs_red
        )
        
        total_abs_ir = (
            hbo2_fraction * self.hbo2_absorption_ir +
            hb_fraction * self.hb_absorption_ir +
            melanin_abs_ir
        )
        
        # Apply Beer-Lambert transmission
        transmission_red = np.exp(-total_abs_red)
        transmission_ir = np.exp(-total_abs_ir)
        
        # DC component (static tissue absorption)
        dc_red = 1.0 * transmission_red
        dc_ir = 1.0 * transmission_ir
        
        # AC component (pulsatile blood volume)
        # Scale by perfusion index
        ac_amplitude_red = 0.02 * transmission_red * perfusion_index
        ac_amplitude_ir = 0.03 * transmission_ir * perfusion_index  # IR has higher AC typically
        
        # Generate final PPG signals
        ppg_red = dc_red + ac_amplitude_red * ppg_base
        ppg_ir = dc_ir + ac_amplitude_ir * ppg_base
        
        # Normalize to 0-1 range for each
        ppg_red = (ppg_red - ppg_red.min()) / (ppg_red.max() - ppg_red.min())
        ppg_ir = (ppg_ir - ppg_ir.min()) / (ppg_ir.max() - ppg_ir.min())
        
        return t, ppg_red, ppg_ir
    
    def estimate_spo2(
        self,
        ppg_red: np.ndarray,
        ppg_ir: np.ndarray
    ) -> float:
        """
        Estimate SpO2 from red and IR PPG signals.
        
        Uses the standard ratio-of-ratios method:
        R = (AC_red/DC_red) / (AC_ir/DC_ir)
        SpO2 = 110 - 25*R (empirical linear calibration)
        
        Args:
            ppg_red: Red wavelength PPG signal
            ppg_ir: Infrared wavelength PPG signal
            
        Returns:
            Estimated SpO2 percentage
        """
        # Calculate AC (pulsatile) and DC (mean) components
        ac_red = np.std(ppg_red)  # AC approximated by standard deviation
        dc_red = np.mean(ppg_red)
        ac_ir = np.std(ppg_ir)
        dc_ir = np.mean(ppg_ir)
        
        # Avoid division by zero
        if dc_red < 0.001 or dc_ir < 0.001 or ac_ir < 0.0001:
            return 0.0
        
        # Calculate R ratio
        r_ratio = (ac_red / dc_red) / (ac_ir / dc_ir)
        
        # Empirical SpO2 calibration (simplified linear model)
        # Real devices use lookup tables from clinical calibration
        spo2 = 110.0 - 25.0 * r_ratio
        
        # Clamp to valid range
        spo2 = np.clip(spo2, 0.0, 100.0)
        
        return spo2
    
    def calculate_r_ratio(
        self,
        ppg_red: np.ndarray,
        ppg_ir: np.ndarray
    ) -> float:
        """Calculate the R ratio used for SpO2 estimation."""
        ac_red = np.std(ppg_red)
        dc_red = np.mean(ppg_red)
        ac_ir = np.std(ppg_ir)
        dc_ir = np.mean(ppg_ir)
        
        if dc_red < 0.001 or dc_ir < 0.001 or ac_ir < 0.0001:
            return 0.0
        
        return (ac_red / dc_red) / (ac_ir / dc_ir)
    
    def run_spo2_stress_test(
        self,
        true_spo2: float = 97.0,
        monk_score: float = 2.0,
        motion_noise: float = 0.0,
        duration_sec: float = 10.0
    ) -> SpO2Result:
        """
        Run a complete SpO2 stress test.
        
        Args:
            true_spo2: Actual oxygen saturation
            monk_score: Monk Skin Tone (1-10)
            motion_noise: Motion artifact level (0-1)
            duration_sec: Signal duration
            
        Returns:
            SpO2Result with detailed metrics
        """
        # Generate clean signals
        t, ppg_red, ppg_ir = self.generate_ppg_dual_wavelength(
            duration_sec=duration_sec,
            true_spo2=true_spo2,
            monk_score=monk_score
        )
        
        # Store clean copies for quality calculation
        clean_red = ppg_red.copy()
        clean_ir = ppg_ir.copy()
        
        # Add motion artifacts if specified
        if motion_noise > 0:
            noise_red = np.random.normal(0, motion_noise * 0.1, len(ppg_red))
            noise_ir = np.random.normal(0, motion_noise * 0.08, len(ppg_ir))
            
            # Baseline wander
            wander = motion_noise * 0.15 * np.sin(2 * np.pi * 0.3 * t)
            
            ppg_red = ppg_red + noise_red + wander
            ppg_ir = ppg_ir + noise_ir + wander * 0.8
        
        # Estimate SpO2
        estimated_spo2 = self.estimate_spo2(ppg_red, ppg_ir)
        r_ratio = self.calculate_r_ratio(ppg_red, ppg_ir)
        
        # Calculate signal quality (correlation with clean)
        quality_red = np.corrcoef(clean_red, ppg_red)[0, 1] if motion_noise > 0 else 1.0
        quality_ir = np.corrcoef(clean_ir, ppg_ir)[0, 1] if motion_noise > 0 else 1.0
        
        return SpO2Result(
            true_spo2=true_spo2,
            estimated_spo2=estimated_spo2,
            bias=estimated_spo2 - true_spo2,
            r_ratio=r_ratio,
            signal_quality_red=quality_red,
            signal_quality_ir=quality_ir
        )
    
    def run_monk_sweep(
        self,
        true_spo2: float = 94.0,
        motion_noise: float = 0.0,
        monk_range: Optional[np.ndarray] = None
    ) -> Dict[str, np.ndarray]:
        """
        Run SpO2 stress test across all Monk skin tones.
        
        Args:
            true_spo2: Actual oxygen saturation (use 94% - clinical threshold)
            motion_noise: Motion artifact level
            monk_range: Array of Monk scores to test (default 1-10)
            
        Returns:
            Dictionary with arrays of results for each Monk score
        """
        if monk_range is None:
            monk_range = np.arange(1, 11)
        
        results = {
            'monk_score': monk_range,
            'estimated_spo2': [],
            'bias': [],
            'r_ratio': [],
            'quality_red': [],
            'quality_ir': []
        }
        
        for monk in monk_range:
            result = self.run_spo2_stress_test(
                true_spo2=true_spo2,
                monk_score=float(monk),
                motion_noise=motion_noise
            )
            
            results['estimated_spo2'].append(result.estimated_spo2)
            results['bias'].append(result.bias)
            results['r_ratio'].append(result.r_ratio)
            results['quality_red'].append(result.signal_quality_red)
            results['quality_ir'].append(result.signal_quality_ir)
        
        # Convert to numpy arrays
        for key in results:
            results[key] = np.array(results[key])
        
        return results


def generate_spo2_bias_report(
    true_spo2: float = 94.0,
    motion_levels: list = None
) -> str:
    """
    Generate a text report of SpO2 bias across Monk skin tones.
    
    Args:
        true_spo2: Ground truth SpO2 (94% is clinical threshold)
        motion_levels: List of motion noise levels to test
        
    Returns:
        Formatted text report
    """
    if motion_levels is None:
        motion_levels = [0.0, 0.5, 1.0]
    
    simulator = SpO2Simulator()
    
    report = []
    report.append("=" * 70)
    report.append("CANDORHEALTH SPO2 BIAS ANALYSIS")
    report.append("=" * 70)
    report.append(f"\nGround Truth SpO2: {true_spo2}%")
    report.append("(94% is the clinical hypoxia threshold)\n")
    
    for motion in motion_levels:
        motion_label = "Stationary" if motion == 0 else f"Motion Level {motion}"
        report.append(f"\n--- {motion_label} ---\n")
        report.append(f"{'Monk':>6} {'Est SpO2':>10} {'Bias':>8} {'Status':>12}")
        report.append("-" * 40)
        
        results = simulator.run_monk_sweep(true_spo2=true_spo2, motion_noise=motion)
        
        for i, monk in enumerate(results['monk_score']):
            est = results['estimated_spo2'][i]
            bias = results['bias'][i]
            
            if abs(bias) > 3.0:
                status = "❌ FAIL"
            elif abs(bias) > 2.0:
                status = "⚠️ WARNING"
            else:
                status = "✓ PASS"
            
            report.append(f"{int(monk):>6} {est:>10.1f}% {bias:>+8.1f}% {status:>12}")
    
    report.append("\n" + "=" * 70)
    report.append("FDA GUIDANCE NOTE")
    report.append("=" * 70)
    report.append("""
Per FDA Draft Guidance (January 2025):
- SpO2 bias > 1% across skin tones may trigger concern
- SpO2 bias > 3% is clinically significant
- Overestimation at true SpO2 = 94% can mask hypoxia

Overestimation on darker skin tones means patients may not receive
supplemental oxygen when they need it — a direct patient safety issue.
""")
    
    return "\n".join(report)
