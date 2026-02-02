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

st.sidebar.markdown("---")
st.sidebar.markdown("### Data Source")

# Try to load real PhysioNet data
REAL_DATA_AVAILABLE = False
try:
    import wfdb
    REAL_DATA_AVAILABLE = True
except ImportError:
    pass

if REAL_DATA_AVAILABLE:
    use_real_data = st.sidebar.checkbox("Use Real PhysioNet PPG", value=True,
                                         help="Load actual human PPG from PhysioNet PTT-PPG dataset")
    if use_real_data:
        ppg_activity = st.sidebar.selectbox("Activity", ["walk", "sit", "run"], index=0)
        st.sidebar.success("✓ Using REAL human PPG data")
    else:
        ppg_activity = None
        st.sidebar.info("Using synthetic PPG model")
else:
    use_real_data = False
    ppg_activity = None
    st.sidebar.warning("wfdb not installed - using synthetic data")

# =============================================================================
# MAIN PANEL
# =============================================================================

# Header
st.markdown('<p class="main-header">CandorHealth Crucible</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Adversarial Validation for PPG & Pulse Oximetry Algorithms</p>', unsafe_allow_html=True)
st.markdown("*Testing optical biosignal robustness across skin tones and real-world conditions*")
st.markdown("---")

# Show data source prominently after signals are loaded (moved display below loading)

# Initialize engine and generate/load signals
data_source_info = ""

# Cached function to load PhysioNet data (persistent cache)
@st.cache_data(ttl=86400, show_spinner="Loading real PPG data from PhysioNet...")  # 24hr cache
def load_physionet_ppg(activity: str):
    """Load and cache PhysioNet PPG data. Cached for 24 hours."""
    record_name = f"s1_{activity}"
    record = wfdb.rdrecord(record_name, pn_dir='pulse-transit-time-ppg/1.1.0')
    
    # Find PPG channel
    ppg_idx = next(i for i, name in enumerate(record.sig_name) if 'pleth' in name.lower())
    
    # Extract 10 seconds from a fixed point (reproducible)
    start_sec = 10
    start_idx = int(start_sec * record.fs)
    end_idx = int((start_sec + 10) * record.fs)
    
    signal = record.p_signal[start_idx:end_idx, ppg_idx]
    signal = (signal - signal.min()) / (signal.max() - signal.min())
    
    return signal, record.fs

# Pre-load common data into session state for instant access
if 'ppg_cache' not in st.session_state:
    st.session_state.ppg_cache = {}

if use_real_data and REAL_DATA_AVAILABLE:
    # Load REAL PPG from PhysioNet (cached)
    try:
        clean_signal, sample_rate = load_physionet_ppg(ppg_activity)
        t = np.arange(len(clean_signal)) / sample_rate
        engine = CandorCrucible(sample_rate=sample_rate)
        data_source_info = f"**Data Source:** PhysioNet PTT-PPG Dataset (Subject 1, {ppg_activity.title()})"
        
    except Exception as e:
        # Fallback to synthetic
        engine = CandorCrucible(sample_rate=125)
        t, clean_signal = engine.generate_synthetic_ppg(duration_sec=10.0, heart_rate=ground_truth_bpm)
        data_source_info = f"**Data Source:** Synthetic PPG (PhysioNet load failed: {str(e)[:30]})"
else:
    # Use synthetic PPG
    engine = CandorCrucible(sample_rate=125)
    t, clean_signal = engine.generate_synthetic_ppg(duration_sec=10.0, heart_rate=ground_truth_bpm)
    data_source_info = "**Data Source:** Synthetic PPG Model (based on physiological waveform characteristics)"

# Display data source prominently
if "PhysioNet" in data_source_info:
    st.success(data_source_info + "\n\n*This is actual human physiological data from peer-reviewed clinical recordings.*")
else:
    st.info(data_source_info)

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

# Cached plot generators for speed
@st.cache_data
def create_ppg_plot(signal_data, color, title, y_limits):
    """Create cached PPG plot."""
    fig, ax = plt.subplots(figsize=(8, 3))
    t_plot = np.arange(len(signal_data)) / 125  # Approximate time axis
    ax.plot(t_plot, signal_data, color=color, linewidth=0.8)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Light Absorption (a.u.)')
    ax.set_ylim(y_limits)
    ax.set_facecolor('#0e1117')
    fig.patch.set_facecolor('#0e1117')
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    for spine in ax.spines.values():
        spine.set_color('white')
    return fig

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Clean PPG Signal (Lab Conditions)")
    # Convert to tuple for hashability
    fig1 = create_ppg_plot(tuple(clean_signal.tolist()), '#28a745', 'Clean', (-0.1, 1.2))
    st.pyplot(fig1)
    plt.close(fig1)

with col2:
    st.markdown("### Degraded PPG Signal (Real-World Conditions)")
    fig2 = create_ppg_plot(tuple(degraded_signal.tolist()), '#dc3545', 'Degraded', (-0.3, 1.5))
    st.pyplot(fig2)
    plt.close(fig2)

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
<strong>📊 Data Source: OpenOximetry Repository</strong><br>
SpO2 bias values shown are derived from <strong>136,518 paired SpO2/SaO2 readings</strong> 
from the OpenOximetry Repository (PhysioNet, Fong et al. 2025). This is <em>measured clinical data</em>, 
not a theoretical model. Each Monk score has thousands of validated samples.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
<strong>Why Skin Tone Affects PPG (The Physics)</strong><br>
PPG uses light (typically red 660nm / IR 940nm) to detect blood volume changes.
Melanin in darker skin absorbs more red light than infrared, artificially lowering 
the R-ratio and causing SpO2 <em>overestimation</em>. This can mask hypoxia.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
<strong>FDA Pulse Oximeter Guidance (January 2025)</strong><br>
Requires testing across Monk Skin Tone scale 1-10 with ≥25% in each cohort (MST 1-4, 5-7, 8-10). 
SpO₂ bias >1% across skin tones may trigger concern; >3% is clinically significant.
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
DATA SOURCE
================================================================================
SpO2 bias model calibrated to OpenOximetry Repository (PhysioNet)
- 136,518 paired SpO2/SaO2 readings with Monk Skin Tone labels
- Source: Fong et al., Scientific Data, 2025
- DOI: 10.13026/be2e-cn29

================================================================================
CandorHealth Crucible v0.4.0 | candorhealth.com
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
# SPO2 BIAS ANALYSIS (The Critical FDA Metric)
# =============================================================================

st.markdown("---")
st.markdown("## 🫁 SpO2 Bias Analysis")
st.markdown("*Oxygen saturation estimation across skin tones — the core FDA concern*")

# SpO2 Simulator - CALIBRATED TO REAL CLINICAL DATA
# 
# Bias values derived from OpenOximetry Repository analysis:
# - 136,518 paired SpO2/SaO2 readings
# - Monk Skin Tone labels from clinical measurements
# - Published: PhysioNet, Feb 2025 (Fong et al.)
#
# This is NOT a model estimate - these are MEASURED values.

class SpO2Simulator:
    """
    SpO2 bias model calibrated to OpenOximetry Repository clinical data.
    
    Source: OpenOximetry Repository v1.1.1 (PhysioNet)
    N = 136,518 paired SpO2/SaO2 readings with Monk Skin Tone labels
    
    Key finding: Pulse oximeters OVERESTIMATE SpO2 across all skin tones,
    with bias increasing in darker skin tones (Monk 7-10).
    """
    
    # REAL measured bias values from OpenOximetry analysis
    # (Mean bias in %, by Monk score 1-10)
    MEASURED_BIAS = {
        1: 0.28,   # N=2,965
        2: 0.74,   # N=15,916
        3: 0.58,   # N=6,879
        4: 0.43,   # N=21,531
        5: 0.74,   # N=22,835
        6: 0.66,   # N=14,712
        7: 1.21,   # N=17,803
        8: 1.57,   # N=23,840
        9: 2.39,   # N=8,782  (WARNING: approaching FDA concern)
        10: 1.45,  # N=1,255
    }
    
    # Standard deviations (shows measurement variability)
    MEASURED_STD = {
        1: 3.20, 2: 2.52, 3: 3.30, 4: 2.94, 5: 3.17,
        6: 4.73, 7: 3.25, 8: 5.06, 9: 4.05, 10: 3.51,
    }
    
    # Sample sizes per Monk score
    SAMPLE_SIZES = {
        1: 2965, 2: 15916, 3: 6879, 4: 21531, 5: 22835,
        6: 14712, 7: 17803, 8: 23840, 9: 8782, 10: 1255,
    }
    
    def __init__(self):
        self.total_samples = sum(self.SAMPLE_SIZES.values())  # 136,518
    
    def calculate_spo2_with_bias(self, true_spo2, monk_score, motion_noise=0.0):
        """
        Calculate the SpO2 that a typical pulse oximeter would REPORT.
        
        Uses ACTUAL measured bias from OpenOximetry Repository (N=136,518).
        
        Args:
            true_spo2: Actual oxygen saturation (from arterial blood gas)
            monk_score: Monk Skin Tone (1-10)
            motion_noise: Additional noise from motion (0-1)
            
        Returns:
            estimated_spo2: What the device would report
            bias: The overestimation amount
        """
        # Get the measured mean bias for this Monk score
        monk_int = int(np.clip(monk_score, 1, 10))
        base_bias = self.MEASURED_BIAS[monk_int]
        measured_std = self.MEASURED_STD[monk_int]
        
        # Bias is slightly amplified in hypoxia (true SpO2 < 94%)
        # This is a conservative adjustment based on literature
        if true_spo2 < 94:
            hypoxia_factor = 1.0 + 0.15 * (94 - true_spo2) / 10.0
            base_bias = base_bias * hypoxia_factor
        
        # Motion increases variability
        motion_std = motion_noise * 1.5
        
        # Add realistic measurement noise (from measured std dev)
        # Use smaller noise for display stability, but real std is available
        noise = np.random.normal(0, min(measured_std * 0.1, 0.5))
        
        total_bias = base_bias + noise + (motion_noise * 0.5)
        
        # Estimated SpO2 (what the device reports)
        estimated_spo2 = true_spo2 + total_bias
        
        # Clamp to valid range
        estimated_spo2 = np.clip(estimated_spo2, 70.0, 100.0)
        
        return estimated_spo2, total_bias
    
    def get_bias_for_monk(self, monk_score):
        """Get the measured mean bias for a Monk score."""
        monk_int = int(np.clip(monk_score, 1, 10))
        return self.MEASURED_BIAS[monk_int]
    
    def generate_dual_wavelength(self, duration_sec, heart_rate, true_spo2, monk_score):
        """Generate visual PPG signals for display (red and IR channels)."""
        sample_rate = 125
        n_samples = int(duration_sec * sample_rate)
        t = np.linspace(0, duration_sec, n_samples)
        fc = heart_rate / 60.0
        
        # Base PPG waveform
        ppg_base = (0.5 * np.sin(2 * np.pi * fc * t) +
                    0.2 * np.sin(2 * np.pi * 2 * fc * t - np.pi/4) +
                    0.1 * np.sin(2 * np.pi * 3 * fc * t))
        
        # Melanin effect: reduces AC amplitude more in red than IR
        melanin_factor = (monk_score - 1) / 9.0
        red_attenuation = 1.0 - 0.4 * melanin_factor
        ir_attenuation = 1.0 - 0.15 * melanin_factor
        
        dc_red = 0.5 * (1.0 - 0.2 * melanin_factor)
        dc_ir = 0.5 * (1.0 - 0.08 * melanin_factor)
        
        ac_red = 0.1 * red_attenuation
        ac_ir = 0.12 * ir_attenuation
        
        ppg_red = dc_red + ac_red * ppg_base
        ppg_ir = dc_ir + ac_ir * ppg_base
        
        ppg_red = (ppg_red - ppg_red.min()) / (ppg_red.max() - ppg_red.min())
        ppg_ir = (ppg_ir - ppg_ir.min()) / (ppg_ir.max() - ppg_ir.min())
        
        return t, ppg_red, ppg_ir
    
    def estimate_spo2(self, ppg_red, ppg_ir):
        """Kept for API compatibility."""
        return 0.0

# SpO2 Controls
spo2_col1, spo2_col2 = st.columns([1, 2])

with spo2_col1:
    true_spo2 = st.slider("True SpO2 (%)", min_value=85, max_value=100, value=94,
                          help="94% is the clinical hypoxia threshold")
    
    st.markdown("""
    <div class="info-box">
    <strong>Why 94%?</strong><br>
    SpO2 < 94% indicates hypoxia requiring intervention.
    Overestimation at this threshold can delay critical treatment.
    </div>
    """, unsafe_allow_html=True)

# SpO2 bias is STATIC (measured from OpenOximetry) - no calculation needed!
# This is a MAJOR performance optimization - just lookup the real values
spo2_sim = SpO2Simulator()
monk_range = np.arange(1, 11)

# Direct lookup from measured data (instant, no calculation)
spo2_biases = np.array([spo2_sim.MEASURED_BIAS[m] for m in range(1, 11)])
spo2_estimates = np.array([true_spo2 + spo2_sim.MEASURED_BIAS[m] for m in range(1, 11)])

@st.cache_data
def create_spo2_bias_chart(true_spo2_val):
    """Cached SpO2 bias chart - only redraws when true_spo2 changes."""
    sim = SpO2Simulator()
    biases = np.array([sim.MEASURED_BIAS[m] for m in range(1, 11)])
    
    fig_spo2, ax_spo2 = plt.subplots(figsize=(10, 5))
    colors = ['#28a745' if abs(b) <= 2 else '#ffc107' if abs(b) <= 3 else '#dc3545' for b in biases]
    ax_spo2.bar(np.arange(1, 11), biases, color=colors, edgecolor='white', linewidth=0.5)
    
    ax_spo2.axhline(y=0, color='white', linestyle='-', linewidth=0.5)
    ax_spo2.axhline(y=2, color='#ffc107', linestyle='--', linewidth=1, label='Warning (2%)')
    ax_spo2.axhline(y=3, color='#dc3545', linestyle='--', linewidth=1, label='FDA Concern (3%)')
    ax_spo2.axhline(y=-2, color='#ffc107', linestyle='--', linewidth=1)
    ax_spo2.axhline(y=-3, color='#dc3545', linestyle='--', linewidth=1)
    
    ax_spo2.set_xlabel('Monk Skin Tone Score', fontsize=11, color='white')
    ax_spo2.set_ylabel('SpO2 Bias (Estimated - True) %', fontsize=11, color='white')
    ax_spo2.set_title(f'SpO2 Estimation Bias by Monk Score (OpenOximetry N=136,518)', 
                      fontsize=12, fontweight='bold', color='white')
    ax_spo2.set_xticks(np.arange(1, 11))
    ax_spo2.set_facecolor('#0e1117')
    fig_spo2.patch.set_facecolor('#0e1117')
    ax_spo2.tick_params(colors='white')
    ax_spo2.legend(loc='upper left', facecolor='#1a1a2e', edgecolor='white', labelcolor='white')
    for spine in ax_spo2.spines.values():
        spine.set_color('white')
    
    return fig_spo2

with spo2_col2:
    # SpO2 Bias Chart (cached)
    fig_spo2 = create_spo2_bias_chart(true_spo2)
    st.pyplot(fig_spo2)
    plt.close(fig_spo2)

# SpO2 Results Table
st.markdown("### SpO2 Bias by Monk Score")
spo2_data = []
for i, monk in enumerate(monk_range):
    bias = spo2_biases[i]
    if abs(bias) <= 2:
        status = "✓ PASS"
    elif abs(bias) <= 3:
        status = "⚠️ WARNING"
    else:
        status = "❌ FAIL"
    spo2_data.append({
        "Monk Score": int(monk),
        "Estimated SpO2": f"{spo2_estimates[i]:.1f}%",
        "Bias": f"{bias:+.1f}%",
        "Status": status
    })

import pandas as pd
spo2_df = pd.DataFrame(spo2_data)
st.dataframe(spo2_df, use_container_width=True, hide_index=True)

# SpO2 Verdict
max_bias = np.max(np.abs(spo2_biases))
if max_bias > 3:
    st.error(f"""
    **❌ SPO2 BIAS FAILURE**
    
    Maximum bias: {max_bias:.1f}% at Monk {monk_range[np.argmax(np.abs(spo2_biases))]}
    
    This exceeds the FDA threshold of 3% and indicates clinically significant 
    overestimation that could mask hypoxia in patients with darker skin tones.
    """)
elif max_bias > 2:
    st.warning(f"""
    **⚠️ SPO2 BIAS WARNING**
    
    Maximum bias: {max_bias:.1f}% at Monk {monk_range[np.argmax(np.abs(spo2_biases))]}
    
    Approaching FDA concern threshold. Additional validation recommended.
    """)
else:
    st.success(f"""
    **✓ SPO2 BIAS ACCEPTABLE**
    
    Maximum bias: {max_bias:.1f}%
    
    Within acceptable limits across all skin tones.
    """)

# =============================================================================
# HIDDEN HYPOXIA RISK CALCULATOR (The Killer Feature)
# =============================================================================

st.markdown("---")
st.markdown("## 🚨 Hidden Hypoxia Risk Calculator")
st.markdown("""
<div class="info-box">
<strong>Clinical Context</strong><br>
"Hidden hypoxia" (occult hypoxemia) occurs when a pulse oximeter displays a safe reading 
while the patient is actually hypoxic. This was a major patient safety issue during COVID-19, 
disproportionately affecting patients with darker skin tones.
<br><br>
<em>Source: Sjoding et al., NEJM 2020 — Black patients had 3x higher rates of occult hypoxemia.</em>
</div>
""", unsafe_allow_html=True)

hypox_col1, hypox_col2 = st.columns([1, 2])

with hypox_col1:
    st.markdown("### Scenario Parameters")
    
    # True (actual) SpO2 - the danger zone
    true_spo2_hypox = st.slider(
        "True Arterial SpO2 (%)",
        min_value=80, max_value=96, value=88,
        help="Actual oxygen saturation from arterial blood gas",
        key="hypox_true_spo2"
    )
    
    # Clinical threshold
    clinical_threshold = st.selectbox(
        "Clinical Decision Threshold",
        options=[94, 92, 90, 88],
        index=0,
        help="SpO2 below this triggers intervention"
    )
    
    st.markdown("""
    **Clinical Thresholds:**
    - **94%**: Start supplemental O₂
    - **92%**: Escalate monitoring
    - **90%**: ICU consideration
    - **88%**: Critical intervention
    """)

# Import scipy for probability calculations
from scipy import stats

# Calculate risk for each Monk score
risk_data = []
for monk in range(1, 11):
    mean_bias = spo2_sim.MEASURED_BIAS[monk]
    std_bias = spo2_sim.MEASURED_STD[monk]
    
    # What device would show (mean)
    device_reading = true_spo2_hypox + mean_bias
    
    # Probability device shows ABOVE threshold (misses hypoxia)
    # Using normal distribution: P(X > threshold)
    z_score = (clinical_threshold - device_reading) / std_bias
    prob_miss = (1 - stats.norm.cdf(z_score)) * 100  # P(device > threshold)
    
    risk_data.append({
        'monk': monk,
        'device_mean': device_reading,
        'prob_miss': prob_miss,
        'std': std_bias,
        'n_samples': spo2_sim.SAMPLE_SIZES[monk]
    })

with hypox_col2:
    st.markdown("### Hidden Hypoxia Risk by Skin Tone")
    
    # Create the risk visualization
    fig_risk, ax_risk = plt.subplots(figsize=(10, 5))
    
    monks = [d['monk'] for d in risk_data]
    probs = [d['prob_miss'] for d in risk_data]
    
    # Color by risk level
    colors = ['#28a745' if p < 20 else '#ffc107' if p < 40 else '#ff6b35' if p < 60 else '#dc3545' for p in probs]
    
    bars = ax_risk.bar(monks, probs, color=colors, edgecolor='white', linewidth=0.5)
    
    # Add percentage labels on bars
    for bar, prob in zip(bars, probs):
        height = bar.get_height()
        ax_risk.annotate(f'{prob:.0f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', color='white', fontsize=10, fontweight='bold')
    
    ax_risk.axhline(y=50, color='#dc3545', linestyle='--', linewidth=2, label='50% Risk')
    ax_risk.axhline(y=25, color='#ffc107', linestyle='--', linewidth=1, label='25% Risk')
    
    ax_risk.set_xlabel('Monk Skin Tone Score', fontsize=12, color='white')
    ax_risk.set_ylabel(f'P(Device Shows ≥{clinical_threshold}%)', fontsize=12, color='white')
    ax_risk.set_title(f'Probability of Missed Hypoxia | True SpO₂ = {true_spo2_hypox}%', 
                      fontsize=13, fontweight='bold', color='white')
    ax_risk.set_xticks(monks)
    ax_risk.set_ylim(0, 105)
    ax_risk.set_facecolor('#0e1117')
    fig_risk.patch.set_facecolor('#0e1117')
    ax_risk.tick_params(colors='white')
    ax_risk.legend(loc='upper left', facecolor='#1a1a2e', edgecolor='white', labelcolor='white')
    for spine in ax_risk.spines.values():
        spine.set_color('white')
    
    st.pyplot(fig_risk)
    plt.close(fig_risk)

# Risk summary table
st.markdown("### Detailed Risk Matrix")

risk_table_data = []
for d in risk_data:
    if d['prob_miss'] < 20:
        risk_level = "🟢 Low"
    elif d['prob_miss'] < 40:
        risk_level = "🟡 Moderate"  
    elif d['prob_miss'] < 60:
        risk_level = "🟠 High"
    else:
        risk_level = "🔴 Critical"
    
    risk_table_data.append({
        "Monk": d['monk'],
        "Device Reading": f"{d['device_mean']:.1f}%",
        "±1σ Range": f"{d['device_mean']-d['std']:.1f}–{d['device_mean']+d['std']:.1f}%",
        f"P(≥{clinical_threshold}%)": f"{d['prob_miss']:.1f}%",
        "Risk": risk_level,
        "N": f"{d['n_samples']:,}"
    })

risk_df = pd.DataFrame(risk_table_data)
st.dataframe(risk_df, use_container_width=True, hide_index=True)

# Clinical interpretation
max_risk = max(risk_data, key=lambda x: x['prob_miss'])
min_risk = min(risk_data, key=lambda x: x['prob_miss'])
risk_ratio = max_risk['prob_miss'] / max(min_risk['prob_miss'], 0.1)

if max_risk['prob_miss'] > 50:
    st.error(f"""
    **⚠️ CRITICAL PATIENT SAFETY FINDING**
    
    At true SpO₂ of **{true_spo2_hypox}%** (hypoxic), patients with **Monk {max_risk['monk']}** skin tone 
    have a **{max_risk['prob_miss']:.0f}% probability** of the device displaying ≥{clinical_threshold}%.
    
    This represents a **{risk_ratio:.1f}x disparity** compared to Monk {min_risk['monk']} ({min_risk['prob_miss']:.0f}%).
    
    *Based on {max_risk['n_samples']:,} clinical measurements from OpenOximetry Repository.*
    """)
elif max_risk['prob_miss'] > 25:
    st.warning(f"""
    **Elevated Disparity Risk**
    
    At true SpO₂ of {true_spo2_hypox}%, Monk {max_risk['monk']} patients have **{max_risk['prob_miss']:.0f}%** 
    probability of appearing above {clinical_threshold}%, vs {min_risk['prob_miss']:.0f}% for Monk {min_risk['monk']}.
    """)
else:
    st.success(f"""
    At true SpO₂ of {true_spo2_hypox}%, hidden hypoxia risk is relatively low across all skin tones 
    (max {max_risk['prob_miss']:.0f}% for Monk {max_risk['monk']}).
    """)

# =============================================================================
# MONK SWEEP BATCH REPORT
# =============================================================================

st.markdown("---")
st.markdown("## 📊 Full Monk Sweep Report")
st.markdown("*Complete validation across all skin tones — the regulatory deliverable*")

if st.button("🔄 Generate Full Monk 1-10 Sweep Report", use_container_width=True):
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    sweep_results = []
    
    for i, monk in enumerate(range(1, 11)):
        status_text.text(f"Testing Monk {monk}/10...")
        progress_bar.progress((i + 1) / 10)
        
        # Generate signals for this Monk score
        t_sweep, clean_sweep = engine.generate_synthetic_ppg(duration_sec=10.0, heart_rate=70)
        
        # Test across motion levels
        for motion_name, (noise, wander) in motion_params.items():
            degraded_sweep = engine.apply_optical_attenuation(clean_sweep.copy(), monk)
            degraded_sweep = engine.apply_motion_artifact(degraded_sweep, noise, wander)
            
            # HR detection
            hr_detected = simple_hr_detection(degraded_sweep, engine.sample_rate)
            hr_error = abs(hr_detected - 70) if hr_detected else None
            
            # SpO2 estimation with proper bias model
            motion_noise_level = {"Stationary": 0.0, "Walking": 0.3, "Running": 0.6, "Exercise": 0.9}
            spo2_est, spo2_bias = spo2_sim.calculate_spo2_with_bias(
                true_spo2=94, 
                monk_score=monk, 
                motion_noise=motion_noise_level.get(motion_name, 0.0)
            )
            
            # Signal quality
            correlation = np.corrcoef(clean_sweep, degraded_sweep)[0, 1]
            
            sweep_results.append({
                "Monk Score": monk,
                "Motion": motion_name,
                "HR Detected": f"{hr_detected:.0f}" if hr_detected else "FAIL",
                "HR Error": f"{hr_error:.0f} BPM" if hr_error else "N/A",
                "SpO2 Est": f"{spo2_est:.1f}%",
                "SpO2 Bias": f"{spo2_bias:+.1f}%",
                "Signal Corr": f"{correlation:.2f}",
                "HR Status": "✓" if (hr_error and hr_error < 10) else "❌",
                "SpO2 Status": "✓" if abs(spo2_bias) < 3 else "❌"
            })
    
    progress_bar.empty()
    status_text.empty()
    
    # Display results
    sweep_df = pd.DataFrame(sweep_results)
    st.dataframe(sweep_df, use_container_width=True, hide_index=True)
    
    # Generate downloadable report
    sweep_report = f"""
================================================================================
CANDORHEALTH CRUCIBLE - FULL MONK SWEEP VALIDATION REPORT
================================================================================

Report Generated: {np.datetime64('now')}
Test Configuration:
  - Monk Skin Tone Range: 1-10 (Full MST Scale)
  - Motion Conditions: Stationary, Walking, Running, Exercise
  - Ground Truth HR: 70 BPM
  - Ground Truth SpO2: 94%

================================================================================
SUMMARY STATISTICS
================================================================================

Total Test Conditions: {len(sweep_results)}
HR Detection Failures: {sum(1 for r in sweep_results if r['HR Status'] == '❌')}
SpO2 Bias Failures: {sum(1 for r in sweep_results if r['SpO2 Status'] == '❌')}

================================================================================
DETAILED RESULTS
================================================================================

{sweep_df.to_string(index=False)}

================================================================================
FDA ALIGNMENT NOTES
================================================================================

Per FDA Draft Guidance on Pulse Oximeter Performance (January 2025):

1. MONK SKIN TONE DISTRIBUTION
   - At least 3,000 paired measurements required
   - Minimum 150 participants across MST scale
   - At least 25% in each cohort (MST 1-4, 5-7, 8-10)

2. PERFORMANCE THRESHOLDS
   - SpO2 bias >1% across skin tones may trigger concern
   - SpO2 bias >3% is clinically significant
   - Overestimation at 94% SpO2 can mask hypoxia

3. MOTION CONDITIONS
   - Real-world validation must include motion artifacts
   - Stationary-only testing is insufficient

================================================================================
DISCLAIMER
================================================================================

This report is for ENGINEERING VALIDATION purposes only.
It does not constitute clinical validation or regulatory submission evidence.
CandorHealth measures signal integrity, not diagnostic accuracy.

================================================================================
CandorHealth Crucible v0.2.0 | candorhealth.com
================================================================================
"""
    
    st.download_button(
        label="📥 Download Full Sweep Report",
        data=sweep_report,
        file_name="candorhealth_monk_sweep_report.txt",
        mime="text/plain",
        use_container_width=True
    )
    
    # CSV export
    csv_sweep = sweep_df.to_csv(index=False)
    st.download_button(
        label="📊 Download Sweep Data (CSV)",
        data=csv_sweep,
        file_name="candorhealth_monk_sweep_data.csv",
        mime="text/csv",
        use_container_width=True
    )

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #6c757d; font-size: 0.9rem;">'
    'CandorHealth Crucible v0.4.0 | SpO2 bias calibrated to OpenOximetry Repository (N=136,518)<br>'
    'For engineering validation only. Not for clinical diagnosis.'
    '</p>',
    unsafe_allow_html=True
)
