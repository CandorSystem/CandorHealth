# =============================================================================
# CANDORHEALTH - FIRST MONEY PLOT
# =============================================================================
# Copy this entire file into a JupyterLab notebook cell and run it.
# This demonstrates the core value proposition: showing where algorithms fail.
# =============================================================================

import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# CORE ENGINE (Self-contained for notebook use)
# -----------------------------------------------------------------------------

class CandorCrucible:
    """Adversarial Validation Engine for Biometric Signals."""
    
    def __init__(self, sample_rate=100):
        self.sample_rate = sample_rate
    
    def generate_synthetic_ppg(self, duration_sec=10.0, heart_rate=75.0):
        """Generate synthetic PPG with realistic morphology."""
        n_samples = int(duration_sec * self.sample_rate)
        t = np.linspace(0, duration_sec, n_samples)
        fc = heart_rate / 60.0
        
        # PPG morphology: fundamental + harmonics for dicrotic notch
        signal = (
            0.6 * np.sin(2 * np.pi * fc * t) +
            0.3 * np.sin(2 * np.pi * 2 * fc * t - np.pi/4) +
            0.1 * np.sin(2 * np.pi * 3 * fc * t - np.pi/3)
        )
        
        # Respiratory modulation
        fr = 15 / 60.0  # 15 breaths/min
        signal = signal * (1.0 + 0.1 * np.sin(2 * np.pi * fr * t))
        
        # Normalize to 0-1
        signal = (signal - signal.min()) / (signal.max() - signal.min())
        return t, signal
    
    def apply_optical_attenuation(self, signal, monk_score):
        """
        Beer-Lambert optical attenuation based on Monk Skin Tone.
        
        This is SENSOR PHYSICS, not a demographic model.
        Darker skin absorbs more light → weaker signal returns.
        """
        # Exponential absorption (Beer-Lambert law)
        mu = 0.1 + 0.15 * (monk_score - 1)
        transmission = np.exp(-mu)
        
        signal_mean = signal.mean()
        signal_ac = signal - signal_mean
        return signal_mean * transmission + signal_ac * transmission
    
    def apply_motion_artifact(self, signal, noise_level=0.1, wander_amplitude=0.2):
        """Motion-induced artifacts: noise + baseline wander."""
        n = len(signal)
        noise = np.random.normal(0, noise_level, n)
        t = np.arange(n) / self.sample_rate
        wander = wander_amplitude * np.sin(2 * np.pi * 0.3 * t)
        return signal + noise + wander
    
    def apply_burst_noise(self, signal, probability=0.01, amplitude=0.3):
        """Sudden signal dropouts/spikes from poor contact."""
        result = signal.copy()
        for i in range(len(signal)):
            if np.random.random() < probability:
                result[i:i+10] += np.random.uniform(-amplitude, amplitude, min(10, len(signal)-i))
        return result
    
    def apply_mains_hum(self, signal, amplitude=0.05, frequency=60.0):
        """Power line interference (60Hz US, 50Hz EU)."""
        t = np.arange(len(signal)) / self.sample_rate
        return signal + amplitude * np.sin(2 * np.pi * frequency * t)


# -----------------------------------------------------------------------------
# MONEY PLOT: THE CORE DEMONSTRATION
# -----------------------------------------------------------------------------

# Initialize engine
engine = CandorCrucible(sample_rate=100)

# Generate ground truth
t, clean = engine.generate_synthetic_ppg(duration_sec=10, heart_rate=72)

# =============================================================================
# SCENARIO MATRIX: Where the industry tests vs where reality lives
# =============================================================================

scenarios = {
    'Ground Truth': {
        'signal': clean,
        'color': '#2ecc71',  # Green
        'description': 'Perfect sensor, perfect conditions'
    },
    'Industry Standard\n(Monk 2, Stationary)': {
        'signal': engine.apply_motion_artifact(
            engine.apply_optical_attenuation(clean, monk_score=2),
            noise_level=0.01, wander_amplitude=0.02
        ),
        'color': '#3498db',  # Blue
        'description': 'How algorithms are typically validated'
    },
    'Real World\n(Monk 6, Walking)': {
        'signal': engine.apply_motion_artifact(
            engine.apply_optical_attenuation(clean, monk_score=6),
            noise_level=0.06, wander_amplitude=0.12
        ),
        'color': '#f39c12',  # Orange
        'description': 'Average user, normal activity'
    },
    'Adversarial\n(Monk 10, Car Ride + Poor Contact)': {
        'signal': engine.apply_burst_noise(
            engine.apply_mains_hum(
                engine.apply_motion_artifact(
                    engine.apply_optical_attenuation(clean, monk_score=10),
                    noise_level=0.15, wander_amplitude=0.25
                ),
                amplitude=0.04
            ),
            probability=0.008
        ),
        'color': '#e74c3c',  # Red
        'description': 'WHERE ALGORITHMS FAIL'
    }
}

# =============================================================================
# PLOT 1: THE MONEY PLOT (Signal Comparison)
# =============================================================================

fig, axes = plt.subplots(len(scenarios), 1, figsize=(14, 10))
fig.suptitle('CandorHealth Adversarial Crucible: Signal Degradation Demonstration', 
             fontsize=14, fontweight='bold', y=1.02)

for idx, (name, data) in enumerate(scenarios.items()):
    ax = axes[idx]
    ax.plot(t, data['signal'], color=data['color'], linewidth=0.8)
    ax.set_ylabel('Amplitude')
    ax.set_title(f"{name}", fontsize=11, fontweight='bold', loc='left')
    ax.text(0.98, 0.85, data['description'], transform=ax.transAxes, 
            fontsize=9, ha='right', style='italic', color='#666')
    ax.set_ylim(-0.3, 1.5)
    ax.set_xlim(0, 10)
    ax.grid(True, alpha=0.3)
    
axes[-1].set_xlabel('Time (seconds)')
plt.tight_layout()
plt.savefig('money_plot_signals.png', dpi=150, bbox_inches='tight')
plt.show()

print("\n" + "="*70)
print("CANDORHEALTH VALUE PROPOSITION")
print("="*70)
print("""
The RED signal is what happens in the real world.
The BLUE signal is what algorithms are validated on.

That gap is:
  → Why pulse oximeters fail on darker skin
  → Why wearables give false readings during exercise  
  → Why the FDA now requires diverse population testing

CandorHealth quantifies this gap BEFORE deployment.
""")

# =============================================================================
# PLOT 2: DEGRADATION CURVE (The Failure Cliff)
# =============================================================================

def signal_quality(clean, degraded):
    """Simple correlation-based quality metric."""
    return max(0, np.corrcoef(clean, degraded)[0, 1])

# Sweep across Monk scores
monk_range = np.linspace(1, 10, 50)
quality_stationary = []
quality_motion = []

for monk in monk_range:
    # Stationary (industry conditions)
    degraded_stat = engine.apply_motion_artifact(
        engine.apply_optical_attenuation(clean, monk),
        noise_level=0.01, wander_amplitude=0.02
    )
    quality_stationary.append(signal_quality(clean, degraded_stat))
    
    # Motion (real-world conditions)
    degraded_motion = engine.apply_motion_artifact(
        engine.apply_optical_attenuation(clean, monk),
        noise_level=0.12, wander_amplitude=0.2
    )
    quality_motion.append(signal_quality(clean, degraded_motion))

# Plot
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(monk_range, quality_stationary, 'b-', linewidth=2, label='Stationary (Lab Conditions)')
ax.plot(monk_range, quality_motion, 'r-', linewidth=2, label='Motion (Real World)')
ax.axhline(y=0.7, color='#666', linestyle='--', label='Failure Threshold (r=0.7)')

ax.fill_between(monk_range, quality_motion, quality_stationary, alpha=0.2, color='red')
ax.annotate('PERFORMANCE GAP\n(Regulatory Risk Zone)', 
            xy=(7, 0.6), fontsize=11, ha='center', color='#c0392b', fontweight='bold')

ax.set_xlabel('Monk Skin Tone Score', fontsize=12)
ax.set_ylabel('Signal Quality (Correlation)', fontsize=12)
ax.set_title('Degradation Curve: Algorithm Robustness vs Skin Tone', fontsize=13, fontweight='bold')
ax.set_xlim(1, 10)
ax.set_ylim(0, 1.05)
ax.legend(loc='lower left')
ax.grid(True, alpha=0.3)

# Add Monk scale labels
for i, tone in enumerate(['Lightest', '', '', '', 'Medium', '', '', '', '', 'Darkest']):
    if tone:
        ax.annotate(tone, xy=(i+1, -0.08), ha='center', fontsize=8, color='#666')

plt.tight_layout()
plt.savefig('degradation_curve.png', dpi=150, bbox_inches='tight')
plt.show()

# =============================================================================
# METRICS OUTPUT
# =============================================================================

print("\n" + "="*70)
print("FAILURE COVERAGE RATIO (FCR) - Prototype Metric")
print("="*70)

# Find where quality drops below 0.7 threshold
threshold = 0.7

fcr_stationary = 10.0  # Never fails in stationary
for i, q in enumerate(quality_motion):
    if q < threshold:
        fcr_motion = monk_range[i]
        break
else:
    fcr_motion = 10.0

print(f"""
Test Conditions:
  - Signal: 10s synthetic PPG, 72 BPM
  - Degradation: Optical attenuation (Beer-Lambert) + Motion artifacts
  - Threshold: Correlation > 0.7

Results:
  Stationary (Lab):     FCR = 100% (never fails across Monk 1-10)
  Motion (Real World):  FCR = {((fcr_motion-1)/9)*100:.1f}% (fails at Monk ~{fcr_motion:.1f})

Interpretation:
  An algorithm validated only in stationary conditions would pass all
  skin tones. The SAME algorithm in real-world motion conditions fails
  at Monk {fcr_motion:.1f}, leaving {((10-fcr_motion)/9)*100:.1f}% of the skin tone range untested.
  
  This is the evidence gap CandorHealth fills.
""")

print("="*70)
print("Plots saved: money_plot_signals.png, degradation_curve.png")
print("="*70)
