"""
CandorHealth Crucible Dashboard
Adversarial Validation Platform for Biometric Algorithms
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="CandorHealth Crucible",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS - Medical Infrastructure Aesthetic
# =============================================================================
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0;
    }
    
    .sub-header {
        font-size: 1rem;
        color: #6c757d;
        margin-top: 0;
    }
    
    /* Metric boxes */
    .metric-pass {
        background-color: #1e3a2f;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    
    .metric-fail {
        background-color: #3a1e1e;
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    
    .metric-warning {
        background-color: #3a3a1e;
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    
    /* Status indicators */
    .status-pass {
        color: #28a745;
        font-size: 3rem;
        font-weight: bold;
    }
    
    .status-fail {
        color: #dc3545;
        font-size: 3rem;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffc107;
        font-size: 3rem;
        font-weight: bold;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1a2e;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #1a1a2e;
        border-left: 4px solid #4a9eff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CRUCIBLE ENGINE (Embedded for standalone operation)
# =============================================================================

class CandorCrucible:
    """Adversarial Validation Engine for Biometric Signals."""
    
    def __init__(self, sample_rate=360):
        self.sample_rate = sample_rate
    
    def generate_synthetic_ppg(self, duration_sec=10.0, heart_rate=70.0):
        """
        Generate synthetic PPG (photoplethysmogram) with realistic morphology.
        
        PPG is an OPTICAL signal - light absorbed/reflected by tissue.
        This is where Beer-Lambert law and skin pigmentation effects apply.
        """
        n_samples = int(duration_sec * self.sample_rate)
        t = np.linspace(0, duration_sec, n_samples)
        fc = heart_rate / 60.0
        
        # PPG morphology using harmonic components
        # Systolic peak (main pulse) + dicrotic notch (reflection wave)
        signal = (
            0.6 * np.sin(2 * np.pi * fc * t) +                    # Fundamental (systolic)
            0.25 * np.sin(2 * np.pi * 2 * fc * t - np.pi/4) +     # 2nd harmonic (dicrotic notch)
            0.1 * np.sin(2 * np.pi * 3 * fc * t - np.pi/3) +      # 3rd harmonic (waveform shape)
            0.05 * np.sin(2 * np.pi * 4 * fc * t - np.pi/2)       # 4th harmonic (fine detail)
        )
        
        # Add respiratory modulation (PPG amplitude varies with breathing)
        fr = 15 / 60.0  # 15 breaths per minute
        respiratory_envelope = 1.0 + 0.08 * np.sin(2 * np.pi * fr * t)
        signal = signal * respiratory_envelope
        
        # Normalize to 0-1 (representing light absorption)
        signal = (signal - signal.min()) / (signal.max() - signal.min())
        
        return t, signal
    
    def apply_optical_attenuation(self, signal, monk_score):
        """Beer-Lambert optical attenuation based on Monk Skin Tone."""
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
        i = 0
        while i < len(signal):
            if np.random.random() < probability:
                burst_len = min(10, len(signal) - i)
                result[i:i+burst_len] += np.random.uniform(-amplitude, amplitude, burst_len)
                i += burst_len
            else:
                i += 1
        return result
    
    def apply_mains_hum(self, signal, amplitude=0.05, frequency=60.0):
        """Power line interference (60Hz US, 50Hz EU)."""
        t = np.arange(len(signal)) / self.sample_rate
        return signal + amplitude * np.sin(2 * np.pi * frequency * t)


def simple_hr_detection(signal, sample_rate):
    """
    Simple peak-based heart rate detection.
    Returns estimated BPM.
    """
    from scipy.signal import find_peaks
    from scipy.ndimage import gaussian_filter1d
    
    # Smooth signal
    smoothed = gaussian_filter1d(signal, sigma=3)
    
    # Find peaks (R-peaks in ECG)
    # Minimum distance between peaks: 0.4 seconds (150 BPM max)
    min_distance = int(0.4 * sample_rate)
    peaks, properties = find_peaks(smoothed, distance=min_distance, height=np.mean(smoothed))
    
    if len(peaks) < 2:
        return None
    
    # Calculate average RR interval
    rr_intervals = np.diff(peaks) / sample_rate  # in seconds
    avg_rr = np.mean(rr_intervals)
    
    # Convert to BPM
    bpm = 60.0 / avg_rr
    
    return bpm


# =============================================================================
# SIDEBAR CONTROLS
# =============================================================================

st.sidebar.markdown("## 🔬 Crucible Controls")
st.sidebar.markdown("---")

# Monk Skin Tone
st.sidebar.markdown("### Optical Absorption (Skin Pigmentation)")
monk_score = st.sidebar.slider(
    "Monk Skin Tone Scale",
    min_value=1,
    max_value=10,
    value=2,
    help="1 = Lightest, 10 = Darkest. Higher melanin content → more light absorption → weaker PPG signal. This is Beer-Lambert physics."
)

# Monk scale visual
monk_colors = ['#f6ede4', '#f3e7db', '#f7ead0', '#eadaba', '#d7bd96', 
               '#a07e56', '#825c43', '#604134', '#3a312a', '#292420']
st.sidebar.markdown(
    f'<div style="background-color: {monk_colors[monk_score-1]}; '
    f'padding: 10px; border-radius: 5px; text-align: center; color: {"#000" if monk_score < 6 else "#fff"}">'
    f'Monk {monk_score}</div>',
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

# Motion Intensity
st.sidebar.markdown("### Motion Conditions")
motion_level = st.sidebar.select_slider(
    "Activity Level",
    options=["Stationary", "Walking", "Running", "Exercise"],
    value="Stationary"
)

motion_params = {
    "Stationary": (0.01, 0.02),
    "Walking": (0.06, 0.12),
    "Running": (0.12, 0.20),
    "Exercise": (0.18, 0.30)
}

# Sensor Contact
st.sidebar.markdown("### Sensor Contact Quality")
contact_quality = st.sidebar.select_slider(
    "Contact Quality",
    options=["Perfect", "Good", "Loose", "Poor"],
    value="Perfect"
)

contact_params = {
    "Perfect": (0.0, 0.0),
    "Good": (0.002, 0.02),
    "Loose": (0.008, 0.04),
    "Poor": (0.015, 0.06)
}

st.sidebar.markdown("---")

# Additional options
st.sidebar.markdown("### Environmental Factors")
add_mains_hum = st.sidebar.checkbox("Add 60Hz Mains Interference", value=False)
mains_amplitude = 0.05 if add_mains_hum else 0.0

st.sidebar.markdown("---")
st.sidebar.markdown("### Ground Truth")
ground_truth_bpm = st.sidebar.number_input("Actual Heart Rate (BPM)", value=70, min_value=40, max_value=200)

# =============================================================================
# MAIN PANEL
# =============================================================================

# Header
st.markdown('<p class="main-header">CandorHealth Crucible</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Adversarial Validation for PPG & Pulse Oximetry Algorithms</p>', unsafe_allow_html=True)
st.markdown("*Testing optical biosignal robustness across skin tones and real-world conditions*")
st.markdown("---")

# Initialize engine and generate signals
# Using 125 Hz - typical PPG sampling rate for wearables
engine = CandorCrucible(sample_rate=125)
t, clean_signal = engine.generate_synthetic_ppg(duration_sec=10.0, heart_rate=ground_truth_bpm)

# Apply degradations based on slider values
noise_level, wander_amp = motion_params[motion_level]
burst_prob, burst_amp = contact_params[contact_quality]

degraded_signal = clean_signal.copy()

# Apply optical attenuation (skin tone)
degraded_signal = engine.apply_optical_attenuation(degraded_signal, monk_score)

# Apply motion artifacts
degraded_signal = engine.apply_motion_artifact(degraded_signal, noise_level, wander_amp)

# Apply contact issues
if burst_prob > 0:
    degraded_signal = engine.apply_burst_noise(degraded_signal, burst_prob, burst_amp)

# Apply mains hum if selected
if add_mains_hum:
    degraded_signal = engine.apply_mains_hum(degraded_signal, mains_amplitude)

# =============================================================================
# SIGNAL VISUALIZATION
# =============================================================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Clean PPG Signal (Lab Conditions)")
    fig1, ax1 = plt.subplots(figsize=(8, 3))
    ax1.plot(t, clean_signal, color='#28a745', linewidth=0.8)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Light Absorption (a.u.)')
    ax1.set_ylim(-0.1, 1.2)
    ax1.set_facecolor('#0e1117')
    fig1.patch.set_facecolor('#0e1117')
    ax1.tick_params(colors='white')
    ax1.xaxis.label.set_color('white')
    ax1.yaxis.label.set_color('white')
    for spine in ax1.spines.values():
        spine.set_color('white')
    st.pyplot(fig1)
    plt.close()

with col2:
    st.markdown("### Degraded PPG Signal (Real-World Conditions)")
    fig2, ax2 = plt.subplots(figsize=(8, 3))
    ax2.plot(t, degraded_signal, color='#dc3545', linewidth=0.8)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Light Absorption (a.u.)')
    ax2.set_ylim(-0.3, 1.5)
    ax2.set_facecolor('#0e1117')
    fig2.patch.set_facecolor('#0e1117')
    ax2.tick_params(colors='white')
    ax2.xaxis.label.set_color('white')
    ax2.yaxis.label.set_color('white')
    for spine in ax2.spines.values():
        spine.set_color('white')
    st.pyplot(fig2)
    plt.close()

# =============================================================================
# FAILURE REPORT
# =============================================================================

st.markdown("---")
st.markdown("## 📊 Algorithm Stress Test Results")

# Detect heart rates
clean_bpm = simple_hr_detection(clean_signal, engine.sample_rate)
degraded_bpm = simple_hr_detection(degraded_signal, engine.sample_rate)

# Calculate errors
clean_error = abs(clean_bpm - ground_truth_bpm) if clean_bpm else None
degraded_error = abs(degraded_bpm - ground_truth_bpm) if degraded_bpm else None

# Display metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Ground Truth")
    st.markdown(f'<div style="font-size: 2.5rem; font-weight: bold; color: #4a9eff;">{ground_truth_bpm} BPM</div>', unsafe_allow_html=True)
    st.markdown("Expected heart rate")

with col2:
    st.markdown("#### Clean Signal Detection")
    if clean_bpm:
        if clean_error < 5:
            st.markdown(f'<div style="font-size: 2.5rem; font-weight: bold; color: #28a745;">{clean_bpm:.1f} BPM</div>', unsafe_allow_html=True)
            st.markdown(f"Error: {clean_error:.1f} BPM ✓")
        else:
            st.markdown(f'<div style="font-size: 2.5rem; font-weight: bold; color: #ffc107;">{clean_bpm:.1f} BPM</div>', unsafe_allow_html=True)
            st.markdown(f"Error: {clean_error:.1f} BPM ⚠️")
    else:
        st.markdown('<div style="font-size: 2.5rem; font-weight: bold; color: #dc3545;">FAILED</div>', unsafe_allow_html=True)

with col3:
    st.markdown("#### Degraded Signal Detection")
    if degraded_bpm:
        if degraded_error < 5:
            st.markdown(f'<div style="font-size: 2.5rem; font-weight: bold; color: #28a745;">{degraded_bpm:.1f} BPM</div>', unsafe_allow_html=True)
            st.markdown(f"Error: {degraded_error:.1f} BPM ✓")
        elif degraded_error < 10:
            st.markdown(f'<div style="font-size: 2.5rem; font-weight: bold; color: #ffc107;">{degraded_bpm:.1f} BPM</div>', unsafe_allow_html=True)
            st.markdown(f"Error: {degraded_error:.1f} BPM ⚠️")
        else:
            st.markdown(f'<div style="font-size: 2.5rem; font-weight: bold; color: #dc3545;">{degraded_bpm:.1f} BPM</div>', unsafe_allow_html=True)
            st.markdown(f"Error: {degraded_error:.1f} BPM ❌")
    else:
        st.markdown('<div style="font-size: 2.5rem; font-weight: bold; color: #dc3545;">FAILED</div>', unsafe_allow_html=True)
        st.markdown("Algorithm could not detect heart rate")

# =============================================================================
# VERDICT BOX
# =============================================================================

st.markdown("---")

# Determine verdict
if degraded_bpm is None:
    verdict = "FAIL"
    verdict_color = "#dc3545"
    verdict_message = "Algorithm failed to detect heart rate under stress conditions"
elif degraded_error > 10:
    verdict = "FAIL"
    verdict_color = "#dc3545"
    verdict_message = f"Clinically significant error: {degraded_error:.1f} BPM deviation"
elif degraded_error > 5:
    verdict = "WARNING"
    verdict_color = "#ffc107"
    verdict_message = f"Elevated error under stress: {degraded_error:.1f} BPM deviation"
else:
    verdict = "PASS"
    verdict_color = "#28a745"
    verdict_message = "Algorithm maintains acceptable accuracy under stress conditions"

# Verdict display
st.markdown(f"""
<div style="
    background-color: {'#3a1e1e' if verdict == 'FAIL' else '#3a3a1e' if verdict == 'WARNING' else '#1e3a2f'};
    border: 3px solid {verdict_color};
    border-radius: 15px;
    padding: 30px;
    text-align: center;
    margin: 20px 0;
">
    <div style="font-size: 4rem; font-weight: bold; color: {verdict_color};">{verdict}</div>
    <div style="font-size: 1.2rem; color: #ffffff; margin-top: 10px;">{verdict_message}</div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# TEST CONDITIONS SUMMARY
# =============================================================================

st.markdown("### Test Conditions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Monk Skin Tone", f"{monk_score}/10")
with col2:
    st.metric("Motion Level", motion_level)
with col3:
    st.metric("Sensor Contact", contact_quality)
with col4:
    st.metric("Signal Correlation", f"{np.corrcoef(clean_signal, degraded_signal)[0,1]:.2f}")

# =============================================================================
# REGULATORY CONTEXT
# =============================================================================

st.markdown("---")
st.markdown("### 📋 Regulatory Context")

st.markdown("""
<div class="info-box">
<strong>Why Skin Tone Affects PPG (The Physics)</strong><br>
PPG uses light (typically green 525nm or red/IR 660nm/940nm) to detect blood volume changes.
Melanin in darker skin absorbs more light (Beer-Lambert Law), reducing the AC component 
of the PPG signal. This is <em>sensor physics</em>, not biology — the same heart produces 
a weaker optical signal through darker skin.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
<strong>FDA Pulse Oximeter Guidance (January 2025)</strong><br>
Requires sponsors to demonstrate algorithm performance across Monk Skin Tone scale 1-10, 
with at least 25% of test participants in each cohort (MST 1-4, 5-7, 8-10). Differences 
greater than 1% SpO₂ bias across skin tones may trigger regulatory concern.
</div>
""", unsafe_allow_html=True)

if monk_score >= 8 and degraded_error and degraded_error > 10:
    st.error("""
    **⚠️ Regulatory Risk Detected**
    
    This algorithm shows >10 BPM error at Monk Skin Tone 8+. Under current FDA guidance, 
    this would likely require additional validation data or algorithm remediation before 
    510(k) clearance.
    """)

# =============================================================================
# EXPORT FUNCTIONALITY
# =============================================================================

st.markdown("---")

# Generate report content
report_content = f"""
================================================================================
CANDORHEALTH CRUCIBLE - ROBUSTNESS VALIDATION REPORT
================================================================================

Report Generated: {np.datetime64('now')}
Signal Type: Photoplethysmogram (PPG)
Duration: 10 seconds
Sample Rate: {engine.sample_rate} Hz

--------------------------------------------------------------------------------
TEST CONDITIONS
--------------------------------------------------------------------------------
Monk Skin Tone Score: {monk_score}/10
Activity Level: {motion_level}
Sensor Contact Quality: {contact_quality}
Environmental Interference: {"60Hz Mains Hum" if add_mains_hum else "None"}
Ground Truth Heart Rate: {ground_truth_bpm} BPM

--------------------------------------------------------------------------------
ALGORITHM PERFORMANCE
--------------------------------------------------------------------------------
Clean Signal Detection: {f"{clean_bpm:.1f} BPM" if clean_bpm else "FAILED"}
Clean Signal Error: {f"{clean_error:.1f} BPM" if clean_error else "N/A"}

Degraded Signal Detection: {f"{degraded_bpm:.1f} BPM" if degraded_bpm else "FAILED"}
Degraded Signal Error: {f"{degraded_error:.1f} BPM" if degraded_error else "N/A"}

Signal Correlation (Clean vs Degraded): {np.corrcoef(clean_signal, degraded_signal)[0,1]:.3f}

--------------------------------------------------------------------------------
VERDICT: {verdict}
--------------------------------------------------------------------------------
{verdict_message}

--------------------------------------------------------------------------------
REGULATORY CONTEXT
--------------------------------------------------------------------------------
FDA Pulse Oximeter Guidance (January 2025) requires:
- Testing across Monk Skin Tone Scale 1-10
- Minimum 25% of participants in each MST cohort (1-4, 5-7, 8-10)
- SpO2 bias differences >1% across skin tones may trigger concern

{"⚠️ WARNING: Algorithm shows >10 BPM error at MST " + str(monk_score) + ". This would likely require additional validation or remediation before 510(k) clearance." if (monk_score >= 8 and degraded_error and degraded_error > 10) else ""}

--------------------------------------------------------------------------------
METHODOLOGY
--------------------------------------------------------------------------------
Signal Degradation Applied:
1. Optical Attenuation (Beer-Lambert Law)
   - Melanin absorption coefficient scaled by Monk score
   - Transmission factor: exp(-μ) where μ = 0.1 + 0.15*(MST-1)

2. Motion Artifacts
   - Gaussian noise (σ = {noise_level:.3f})
   - Baseline wander (amplitude = {wander_amp:.3f}, freq = 0.3 Hz)

3. Sensor Contact Artifacts
   - Burst noise probability: {burst_prob:.4f}
   - Burst amplitude: {burst_amp:.3f}

{"4. Power Line Interference (60 Hz, amplitude = 0.05)" if add_mains_hum else ""}

--------------------------------------------------------------------------------
DISCLAIMER
--------------------------------------------------------------------------------
This report is for ENGINEERING VALIDATION purposes only.
It does not constitute clinical validation or regulatory submission evidence.
CandorHealth measures signal integrity, not diagnostic accuracy.

================================================================================
CandorHealth Crucible v0.1.0 | candorhealth.com
================================================================================
"""

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="📄 Download Validation Report",
        data=report_content,
        file_name=f"candorhealth_report_monk{monk_score}_{motion_level.lower()}.txt",
        mime="text/plain",
        use_container_width=True
    )

with col2:
    # CSV export of signal data
    import pandas as pd
    signal_df = pd.DataFrame({
        'time_sec': t,
        'clean_signal': clean_signal,
        'degraded_signal': degraded_signal
    })
    csv_data = signal_df.to_csv(index=False)
    
    st.download_button(
        label="📊 Download Signal Data (CSV)",
        data=csv_data,
        file_name=f"candorhealth_signals_monk{monk_score}_{motion_level.lower()}.csv",
        mime="text/csv",
        use_container_width=True
    )

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #6c757d; font-size: 0.9rem;">'
    'CandorHealth Crucible v0.1.0 | Adversarial Validation Infrastructure for Biometric Algorithms<br>'
    'For engineering validation only. Not for clinical diagnosis.'
    '</p>',
    unsafe_allow_html=True
)
