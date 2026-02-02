# CandorHealth

**Adversarial Validation Infrastructure for Biometric Algorithms**

CandorHealth is a compliance firewall and red-team platform for biometric algorithms. It quantifies where algorithms fail under real-world conditions, providing regulator-aligned robustness evidence.

## What CandorHealth Does

- **Systematically degrades** biometric signals using physics-grounded transformations
- **Quantifies algorithm failure** under realistic sensor and environmental conditions
- **Produces compliance evidence** aligned with FDA guidance on algorithm robustness

## What CandorHealth Does NOT Do

- Simulate patients or disease
- Predict health outcomes
- Make diagnostic claims
- Replace clinical validation

CandorHealth studies **signal integrity**, not human health.

## Project Structure

```
CandorHealth/
├── candor/                    # Core Python package
│   ├── __init__.py
│   ├── crucible.py           # Signal Degradation Engine
│   └── metrics.py            # FCR and robustness metrics
├── notebooks/
│   └── 01_money_plot.py      # Demo notebook (paste into JupyterLab)
├── requirements.txt
└── README.md
```

## Quick Start

### Local Development

```bash
pip install -r requirements.txt
python -c "from candor import CandorCrucible; print('Engine ready')"
```

### GCP Vertex AI

1. Open your Vertex AI Workbench notebook
2. Copy contents of `notebooks/01_money_plot.py` into a cell
3. Run to generate money plots

## Core Concepts

### Signal Degradation Engine

Applies controlled, physics-grounded transformations:

- **Optical attenuation** (Beer-Lambert) — models skin pigmentation effects on PPG
- **Motion artifacts** — Gaussian noise + baseline wander
- **Burst noise** — sensor contact issues
- **Mains hum** — 50/60Hz power line interference
- **Sampling jitter** — ADC timing irregularities

### Failure Coverage Ratio (FCR)

Proprietary metric measuring the proportion of realistic failure space an algorithm has been tested against. Reframes validation from "accuracy" to **resilience**.

## Regulatory Alignment

Designed to support evidence requirements from:

- FDA Draft Guidance on Pulse Oximeter Performance (Jan 2025)
- FDA AI-Enabled Device Software Functions Guidance (Jan 2025)
- EU AI Act (2024) high-risk classification requirements

## License

Proprietary - CandorHealth Inc.
